"""Orquesta SfM COLMAP, exportación dispersa y densificación opcional.

No instala COLMAP. La densificación puede requerir CUDA.
"""
import argparse
import json
import time
from pathlib import Path

from .motor_colmap import ejecutar_colmap
from .colmap_denso import densificar_colmap


def pipeline_colmap(fotos, salida, ejecutable="colmap", gpu=False,
                    denso=False, modelo="0", timeout_segundos=14400):
    inicio_pipeline = time.monotonic()
    if type(timeout_segundos) is not int or timeout_segundos <= 0:
        raise ValueError("Timeout total inválido")
    limite_global = inicio_pipeline + timeout_segundos
    fotos = Path(fotos)
    salida = Path(salida)
    informe = ejecutar_colmap(fotos, salida, ejecutable=ejecutable,
                              usar_gpu=gpu, timeout_segundos=timeout_segundos)
    resultado = {"motor": "COLMAP", "disperso": informe,
                 "denso_solicitado": bool(denso), "denso": None,
                 "presupuesto_total_segundos": timeout_segundos}
    if denso:
        restante = int(limite_global - time.monotonic())
        if restante <= 0:
            resultado["error_denso"] = "Presupuesto total de procesamiento agotado antes de iniciar fase densa"
        else:
            try:
                resultado["denso"] = densificar_colmap(
                    salida, fotos, modelo=modelo, ejecutable=ejecutable,
                    timeout_segundos=restante)
                except (RuntimeError, ValueError, FileNotFoundError) as exc:
                resultado["error_denso"] = str(exc)
    resultado["duracion_total_segundos"] = round(time.monotonic() - inicio_pipeline, 3)
    (salida / "pipeline_colmap.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    return resultado


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("fotos", type=Path)
    p.add_argument("--salida", required=True, type=Path)
    p.add_argument("--colmap", default="colmap")
    p.add_argument("--gpu", action="store_true")
    p.add_argument("--denso", action="store_true")
    p.add_argument("--modelo", default="0")
    p.add_argument("--timeout", type=int, default=14400)
    args = p.parse_args()
    resultado = pipeline_colmap(args.fotos, args.salida, args.colmap,
                               args.gpu, args.denso, args.modelo, args.timeout)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    if args.denso and "error_denso" in resultado:
        p.exit(2, "La fase densa falló; consultar pipeline_colmap.json\n")


if __name__ == "__main__":
    main()
