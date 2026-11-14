"""Adaptador experimental de la cola persistente a pipeline_colmap.

No sustituye al servidor actual. Ejecutar solamente en entorno controlado.
Cada trabajo necesita fotos previamente cargadas en <base>/entradas/<id>/fotos.
"""
from pathlib import Path

from tools.pipeline_colmap import pipeline_colmap
from tools.worker_resultados import ejecutar_con_resultados


def procesar_colmap(cola, base, worker, *, ejecutable="colmap", gpu=False,
                    denso=False, timeout_segundos=14400, segundos_lease=300,
                    max_intentos=3):
    base = Path(base).resolve()

    def ejecutar(id_trabajo, carpeta):
        fotos = base / "entradas" / id_trabajo / "fotos"
        if not fotos.is_dir() or fotos.is_symlink():
            raise FileNotFoundError("No se encontraron fotografías del trabajo")
        if not any(fotos.iterdir()):
            raise ValueError("La carpeta de fotografías está vacía")
        pipeline_colmap(fotos, carpeta, ejecutable=ejecutable, gpu=gpu,
                        denso=denso, timeout_segundos=timeout_segundos)

    return ejecutar_con_resultados(
        cola, base, worker, ejecutar, segundos_lease=segundos_lease,
        max_intentos=max_intentos)
