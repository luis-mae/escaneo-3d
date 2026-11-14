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
        entradas = base / "entradas"
        proyecto = entradas / id_trabajo
        fotos = proyecto / "fotos"
        if entradas.is_symlink() or proyecto.is_symlink():
            raise ValueError("Directorio de entrada no confiable")
        if not fotos.is_dir() or fotos.is_symlink() or not fotos.resolve().is_relative_to(proyecto.resolve()):
            raise FileNotFoundError("No se encontraron fotografías del trabajo")
        archivos = list(fotos.iterdir())
        if any(f.is_symlink() or not f.is_file() for f in archivos):
            raise ValueError("La carpeta contiene enlaces o directorios")
        if not 3 <= len(archivos) <= 100:
            raise ValueError("Cantidad de fotografías fuera de rango")
        if any(f.suffix.lower() not in (".jpg", ".jpeg", ".png") for f in archivos):
            raise ValueError("La carpeta contiene archivos no admitidos")
        if any(f.stat().st_size == 0 or f.stat().st_size > 20 * 1024 * 1024 for f in archivos):
            raise ValueError("Fotografía vacía o demasiado grande")
        if sum(f.stat().st_size for f in archivos) > 500 * 1024 * 1024:
            raise ValueError("Tamaño total de fotografías excedido")
        pipeline_colmap(fotos, carpeta, ejecutable=ejecutable, gpu=gpu,
                        denso=denso, timeout_segundos=timeout_segundos,
                        cancel_event=cancel_event)
        # Un retorno sin excepción no garantiza que COLMAP haya producido
        # una nube utilizable. No publicar ni completar trabajos vacíos.
        candidatos = [carpeta / "dense_0" / "fused.ply", *carpeta.glob("modelo_*.ply")]
        if not any(p.is_file() and not p.is_symlink() and p.stat().st_size > 0 and
                   p.resolve().is_relative_to(carpeta.resolve()) for p in candidatos):
            raise RuntimeError("COLMAP terminó sin generar una nube PLY válida")

    return ejecutar_con_resultados(
        cola, base, worker, ejecutar, segundos_lease=segundos_lease,
        max_intentos=max_intentos, pasar_cancelacion=True)
