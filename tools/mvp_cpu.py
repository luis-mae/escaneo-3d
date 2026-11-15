"""Pipeline local CPU: fotos -> fondo opcional -> COLMAP -> OBJ -> STL/PLY.

Ejemplo (desde raíz del repositorio):
 python -m tools.mvp_cpu --fotos A:\\escaneo3d\\fotos --salida A:\\escaneo3d\\resultado_mvp --colmap colmap --quitar-fondo

Requiere COLMAP en PATH, numpy/scipy y dependencias del repositorio.
--quitar-fondo requiere además rembg[cpu] y Pillow.
No reemplaza reconstrucción densa ni garantiza una malla fiel/imprimible.
"""
import argparse
import json
from pathlib import Path

from .motor_colmap import ejecutar_colmap
from .superficie_automatica import reconstruir_superficie_auto
from .colmap_a_malla import nube_colmap_a_malla
from .exportar_formatos_3d import exportar_formatos


def ejecutar_mvp(fotos, salida, colmap="colmap", quitar_fondo=False,
                timeout=14400, max_puntos=12000):
    fotos = Path(fotos).resolve()
    salida = Path(salida).resolve()
    if not fotos.is_dir():
        raise FileNotFoundError(fotos)
    if salida.exists():
        raise FileExistsError("Elegí una carpeta de salida nueva para no sobrescribir datos")
    if salida == fotos or salida in fotos.parents or fotos in salida.parents:
        raise ValueError("Fotos y resultados deben estar en carpetas separadas")
    if timeout <= 0 or max_puntos < 4:
        raise ValueError("Parámetros de tiempo o puntos inválidos")
    salida.mkdir(parents=True)
    informe = {"estado": "iniciado", "fotos": str(fotos), "salida": str(salida)}
    try:
        imagenes = fotos
        if quitar_fondo:
            from .quitar_fondo import process_folder
            imagenes = salida / "imagenes"
            informe["imagenes_procesadas"] = process_folder(
                fotos, imagenes, salida / "mascaras")
            # El adaptador COLMAP existente no consume máscaras; las imágenes
            # RGB ya tienen fondo negro. No afirmar filtrado de features por máscara.
        informe["estado"] = "colmap"
        reconstruccion = salida / "colmap"
        colmap_info = ejecutar_colmap(imagenes, reconstruccion, ejecutable=colmap,
                                     usar_gpu=False, timeout_segundos=timeout)
        validos = [e for e in colmap_info["exportaciones_ply"] if e.get("exportado")]
        if not validos:
            raise RuntimeError("COLMAP no generó una nube PLY utilizable")
        mejor = max(validos, key=lambda e: e.get("vertices", 0))
        nube = reconstruccion / mejor["ply"]
        informe["nube_ply"] = str(nube)
        informe["puntos_colmap"] = mejor.get("vertices", 0)
        informe["estado"] = "superficie"
        malla = salida / "superficie.obj"
        try:
            superficie = reconstruir_superficie_auto(nube, malla, max_puntos=max_puntos)
        except (ValueError, RuntimeError, MemoryError) as exc:
            informe["error_alpha"] = str(exc)
            # Respaldo explícito: puede ser una envolvente convexa aproximada.
            superficie = nube_colmap_a_malla(
                nube, malla, alpha=1.0, max_puntos=max_puntos)
        informe["superficie"] = superficie
        informe["estado"] = "exportaciones"
        informe["exportaciones"] = exportar_formatos(
            malla, salida / "exportaciones", ("obj", "stl", "ply", "glb"))
        informe["estado"] = "completado"
        informe["advertencia"] = (
            "Malla experimental desde nube dispersa; escala arbitraria, "
            "sin texturas ni precisión certificada. Revisar antes de imprimir.")
        return informe
    except Exception as exc:
        informe["estado"] = "fallido"
        informe["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        (salida / "resultado_mvp.json").write_text(
            json.dumps(informe, ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fotos", type=Path, required=True)
    p.add_argument("--salida", type=Path, required=True)
    p.add_argument("--colmap", default="colmap")
    p.add_argument("--quitar-fondo", action="store_true")
    p.add_argument("--timeout", type=int, default=14400)
    p.add_argument("--max-puntos", type=int, default=12000)
    args = p.parse_args()
    print(json.dumps(ejecutar_mvp(
        args.fotos, args.salida, args.colmap, args.quitar_fondo,
        args.timeout, args.max_puntos), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
