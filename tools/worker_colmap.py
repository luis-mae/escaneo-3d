"""Adaptador experimental de la cola persistente a pipeline_colmap.

No sustituye al servidor actual. Ejecutar solamente en entorno controlado.
Cada trabajo necesita fotos previamente cargadas en <base>/entradas/<id>/fotos.
"""
from pathlib import Path
import re

from tools.pipeline_colmap import pipeline_colmap
from tools.worker_resultados import ejecutar_con_resultados


def procesar_colmap(cola, base, worker, *, ejecutable="colmap", gpu=False,
                    denso=False, timeout_segundos=14400, segundos_lease=300,
                    max_intentos=3):
    base = Path(base).resolve()

    def ejecutar(id_trabajo, carpeta, cancel_event):
        if not re.fullmatch(r"[a-f0-9]{32}", id_trabajo):
            raise ValueError("ID de trabajo inválido")
        fotos = base / "entradas" / id_trabajo / "fotos"
        if not fotos.is_dir() or fotos.is_symlink() or not fotos.resolve().is_relative_to(base / "entradas" / id_trabajo):
            raise FileNotFoundError("No se encontraron fotografías del trabajo")
        archivos = list(fotos.iterdir())
        if not archivos or len(archivos) > 100:
            raise ValueError("Cantidad de fotografías fuera de rango")
        if any(not f.is_file() or f.is_symlink() or f.suffix.lower() not in (".jpg", ".jpeg", ".png") for f in archivos):
            raise ValueError("La carpeta contiene archivos no admitidos")
        if not any(f.is_file() and not f.is_symlink() and f.suffix.lower() in (".jpg", ".jpeg", ".png") for f in archivos):
            raise ValueError("La carpeta de fotografías está vacía")
        pipeline_colmap(fotos, carpeta, ejecutable=ejecutable, gpu=gpu,
                        denso=denso, timeout_segundos=timeout_segundos,
                        cancel_event=cancel_event)

    return ejecutar_con_resultados(
        cola, base, worker, ejecutar, segundos_lease=segundos_lease,
        max_intentos=max_intentos, pasar_cancelacion=True)
