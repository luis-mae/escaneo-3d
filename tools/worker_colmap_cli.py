"""Ejecuta un único trabajo de cola persistente en un entorno local confiable.

Ejemplo:
 python -m tools.worker_colmap_cli --base datos_worker --worker nodo-1
No expone un servidor ni habilita procesamiento remoto público.
"""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from tools.cola_persistente import ColaPersistente
from tools.worker_colmap import procesar_colmap


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base", type=Path, required=True)
    p.add_argument("--worker", required=True)
    p.add_argument("--colmap", default="colmap")
    p.add_argument("--gpu", action="store_true")
    p.add_argument("--denso", action="store_true")
    p.add_argument("--timeout", type=int, default=14400)
    p.add_argument("--lease", type=int, default=300)
    p.add_argument("--intentos", type=int, default=3)
    args = p.parse_args(argv)
    if not args.worker.strip() or len(args.worker) > 128:
        p.error("Identificador de worker inválido")
    if args.timeout <= 0 or args.lease < 3 or args.intentos < 1:
        p.error("Timeout, lease o intentos inválidos")
    if shutil.which(args.colmap) is None:
        p.error("No se encontró el ejecutable COLMAP")
    base = args.base.resolve()
    cola = ColaPersistente(base / "cola.sqlite")
    resultado = procesar_colmap(
        cola, base, args.worker, ejecutable=args.colmap, gpu=args.gpu,
        denso=args.denso, timeout_segundos=args.timeout,
        segundos_lease=args.lease, max_intentos=args.intentos,
    )
    print(json.dumps({"id_trabajo": resultado.id_trabajo, "estado": resultado.estado}))
    return 0 if resultado.estado in ("sin_trabajos", "completado") else 1


if __name__ == "__main__":
    sys.exit(main())
