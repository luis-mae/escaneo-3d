"""MVP local completo: fotos -> COLMAP -> nube PLY -> OBJ/STL/GLB.

Requiere COLMAP instalado en PATH. No garantiza escala ni impresión 3D.
Ejemplo:
 python -m tools.escanear_fotos_mvp ./fotos --salida ./escaneo_resultado
"""
import argparse
import json
import math
from pathlib import Path

from .motor_colmap import ejecutar_colmap, _cantidad_vertices_ply
from .procesar_nube_mvp import procesar_nube_mvp
from .verificar_sesion_mvp import verificar_sesion


def escanear_fotos_mvp(fotos, salida, colmap="colmap", usar_gpu=False,
                      timeout_segundos=7200, max_puntos=2500, alpha=None):
    fotos, salida = Path(fotos).resolve(), Path(salida).resolve()
    if salida.exists():
        raise FileExistsError("La carpeta de salida ya existe")
    if not fotos.is_dir():
        raise ValueError("La carpeta de fotografías no existe")
    if salida == fotos or salida in fotos.parents or fotos in salida.parents:
        raise ValueError("La salida debe estar separada de las fotografías")
    if type(max_puntos) is not int or not 4 <= max_puntos <= 10000:
        raise ValueError("max_puntos debe estar entre 4 y 10000")
    if type(timeout_segundos) is not int or timeout_segundos <= 0:
        raise ValueError("Tiempo máximo inválido")
    if alpha is not None and (not math.isfinite(alpha) or alpha <= 0):
        raise ValueError("Alpha inválido")
    # El motor valida las fotos y crea una salida nueva sin sobrescribir.
    try:
        reconstruccion = ejecutar_colmap(
            fotos, salida / "colmap", ejecutable=colmap, usar_gpu=usar_gpu,
            timeout_segundos=timeout_segundos,
        )
    except Exception as exc:
        # COLMAP puede fallar antes de crear la carpeta (por ejemplo, sin ejecutable).
        salida.mkdir(parents=True, exist_ok=True)
        (salida / "ERROR_COLMAP.txt").write_text(
            f"{type(exc).__name__}: {exc}\n", encoding="utf-8"
        )
        raise
    exportaciones = reconstruccion.get("exportaciones_ply", [])
    candidatas = []
    for item in exportaciones:
        if item.get("exportado"):
            nombre = item.get("ply")
            if not isinstance(nombre, str) or not nombre.endswith(".ply"):
                continue
            raiz_colmap = (salida / "colmap").resolve()
            ruta = (raiz_colmap / nombre).resolve()
            if ruta.is_relative_to(raiz_colmap) and ruta.is_file() and _cantidad_vertices_ply(ruta) >= 4:
                candidatas.append(ruta)
    if not candidatas:
        salida.mkdir(parents=True, exist_ok=True)
        (salida / "ERROR_NUBE.txt").write_text(
            "COLMAP no produjo una nube PLY con al menos cuatro puntos. "
            "Revisar colmap/informe_colmap.json.\n", encoding="utf-8"
        )
        raise RuntimeError("COLMAP no produjo una nube PLY utilizable")
    nube = max(candidatas, key=_cantidad_vertices_ply)
    try:
        malla = procesar_nube_mvp(
            nube, salida / "modelo_3d", alpha=alpha, max_puntos=max_puntos,
        )
    except Exception as exc:
        (salida / "ERROR_MALLA.txt").write_text(
            f"COLMAP terminó, pero falló el mallado: {type(exc).__name__}: {exc}\n",
            encoding="utf-8",
        )
        raise
    # Un PLY disperso puede producir una malla matemática sin reproducir el objeto.
    calidad = "preliminar_no_validada"
    if malla.get("geometria_de_respaldo"):
        calidad = "solo_envolvente_convexa"
    resumen = {
        "calidad_geometrica": calidad,
        "apto_para_impresion": False,
        "fotografias": str(fotos),
        "nube_colmap": str(nube),
        "modelos_reconstruidos": len(reconstruccion.get("modelos_dispersos", [])),
        "mallado": malla,
        "archivos": {
            formato: str(salida / "modelo_3d" / "exportados" / f"modelo.{formato}")
            for formato in ("obj", "stl", "glb")
        },
        "advertencia": "La nube COLMAP es dispersa: el OBJ/STL/GLB generado NO demuestra reconstrucción fiel del objeto; escala física no calibrada ni impresión validada.",
    }
    (salida / "resultado_mvp.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return resumen



def reanudar_sesion_mvp(sesion, salida, alpha=None, max_puntos=2500):
    """Reutiliza una nube PLY existente sin ejecutar COLMAP ni modificar la sesión."""
    sesion, salida = Path(sesion).resolve(), Path(salida).resolve()
    if not sesion.is_dir():
        raise ValueError("La sesión anterior no existe")
    if salida.exists():
        raise FileExistsError("La carpeta de salida ya existe")
    if salida == sesion or salida in sesion.parents or sesion in salida.parents:
        raise ValueError("La salida debe estar separada de la sesión")
    if type(max_puntos) is not int or not 4 <= max_puntos <= 10000:
        raise ValueError("max_puntos debe estar entre 4 y 10000")
    if alpha is not None and (not math.isfinite(alpha) or alpha <= 0):
        raise ValueError("Alpha inválido")
    reporte = verificar_sesion(sesion)
    nube = reporte["reutilizar_nube"]
    if not nube:
        raise ValueError("La sesión no contiene ninguna nube PLY reutilizable")
    salida.mkdir(parents=True)
    try:
        malla = procesar_nube_mvp(
            Path(nube), salida / "modelo_3d", alpha=alpha, max_puntos=max_puntos
        )
    except Exception as exc:
        (salida / "ERROR_MALLA.txt").write_text(
            f"{type(exc).__name__}: {exc}\n", encoding="utf-8"
        )
        raise
    origen_denso = Path(nube).name.lower() == "fused.ply"
    resumen = {
        "tipo_nube": "densa" if origen_denso else "dispersa_o_desconocida",
        "control_calidad": malla.get("control_calidad", {}),
        "calidad_geometrica": (
            "solo_envolvente_convexa" if malla.get("geometria_de_respaldo")
            else "preliminar_no_validada"
        ),
        "apto_para_impresion": False,
        "modo": "reanudar_sin_colmap",
        "sesion_original": str(sesion),
        "nube_colmap": nube,
        "mallado": malla,
        "archivos": {
            formato: str(salida / "modelo_3d" / "exportados" / f"modelo.{formato}")
            for formato in ("obj", "stl", "glb")
        },
        "advertencia": (
            "Se reutilizó una nube densa; su geometría y escala aún requieren "
            "validación visual y dimensional."
            if origen_denso else
            "Se reutilizó una nube dispersa o de densidad desconocida: "
            "la malla no garantiza reproducir el objeto; escala no calibrada."
        ),
    }
    (salida / "resultado_mvp.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return resumen


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("fotos", type=Path, help="Fotos o carpeta de sesión si se usa --reanudar")
    p.add_argument("--reanudar", action="store_true", help="Usar PLY de sesión existente sin ejecutar COLMAP")
    p.add_argument("--salida", type=Path, required=True)
    p.add_argument("--colmap", default="colmap")
    p.add_argument("--gpu", action="store_true")
    p.add_argument("--timeout", type=int, default=7200)
    p.add_argument("--max-puntos", type=int, default=2500)
    p.add_argument("--alpha", type=float)
    args = p.parse_args()
    if args.reanudar:
        resultado = reanudar_sesion_mvp(args.fotos, args.salida, args.alpha, args.max_puntos)
    else:
        resultado = escanear_fotos_mvp(
            args.fotos, args.salida, args.colmap, args.gpu,
            args.timeout, args.max_puntos, args.alpha,
        )
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
