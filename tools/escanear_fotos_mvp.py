"""MVP local completo: fotos -> COLMAP -> nube PLY -> OBJ/STL/GLB.

Requiere COLMAP instalado en PATH. No garantiza escala ni impresión 3D.
Ejemplo:
 python -m tools.escanear_fotos_mvp ./fotos --salida ./escaneo_resultado
"""
import argparse
import json
from pathlib import Path

from .motor_colmap import ejecutar_colmap, _cantidad_vertices_ply
from .procesar_nube_mvp import procesar_nube_mvp


def escanear_fotos_mvp(fotos, salida, colmap="colmap", usar_gpu=False,
                      timeout_segundos=7200, max_puntos=2500, alpha=None):
    fotos, salida = Path(fotos).resolve(), Path(salida).resolve()
    if salida.exists():
        raise FileExistsError("La carpeta de salida ya existe")
    # El motor valida las fotos y crea una salida nueva sin sobrescribir.
    reconstruccion = ejecutar_colmap(
        fotos, salida / "colmap", ejecutable=colmap, usar_gpu=usar_gpu,
        timeout_segundos=timeout_segundos,
    )
    exportaciones = reconstruccion.get("exportaciones_ply", [])
    candidatas = []
    for item in exportaciones:
        if item.get("exportado"):
            ruta = salida / "colmap" / item["ply"]
            if ruta.is_file():
                candidatas.append(ruta)
    if not candidatas:
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
    resumen = {
        "fotografias": str(fotos),
        "nube_colmap": str(nube),
        "modelos_reconstruidos": len(reconstruccion.get("modelos_dispersos", [])),
        "mallado": malla,
        "archivos": {
            formato: str(salida / "modelo_3d" / "exportados" / f"modelo.{formato}")
            for formato in ("obj", "stl", "glb")
        },
        "advertencia": "Escala física no verificada; la calidad requiere inspección visual.",
    }
    (salida / "resultado_mvp.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return resumen


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("fotos", type=Path)
    p.add_argument("--salida", type=Path, required=True)
    p.add_argument("--colmap", default="colmap")
    p.add_argument("--gpu", action="store_true")
    p.add_argument("--timeout", type=int, default=7200)
    p.add_argument("--max-puntos", type=int, default=2500)
    p.add_argument("--alpha", type=float)
    args = p.parse_args()
    print(json.dumps(escanear_fotos_mvp(
        args.fotos, args.salida, args.colmap, args.gpu,
        args.timeout, args.max_puntos, args.alpha,
    ), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
