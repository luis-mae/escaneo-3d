"""Orquestación experimental de worker con staging y publicación.

El callback recibe (id_trabajo, carpeta_staging) y debe escribir solo allí.
No conecta COLMAP ni cuotas; no habilitar procesamiento remoto público.
"""
from pathlib import Path
import shutil

from tools.resultados_aislados import preparar, publicar
from tools.worker_base import ejecutar_uno


def ejecutar_con_resultados(cola, base, worker, procesar, *, segundos_lease=300, max_intentos=3, pasar_cancelacion=False):
    """Ejecuta un trabajo aislando archivos por token; exige worker exclusivo."""
    def ejecutar(id_trabajo, cancel_event, token):
        if not cola.estado_reclamo(id_trabajo, worker, token):
            raise RuntimeError("Lease perdido antes de preparar resultados")
        carpeta = preparar(base, id_trabajo, token)
        try:
            if pasar_cancelacion:
                procesar(id_trabajo, Path(carpeta), cancel_event)
            else:
                procesar(id_trabajo, Path(carpeta))
            publicar(base, id_trabajo, worker, token, cola)
        finally:
            # La publicación mueve el staging; si falla o se pierde el
            # lease, eliminar el temporal sin tocar resultados publicados.
            if Path(carpeta).exists():
                shutil.rmtree(carpeta)
    return ejecutar_uno(cola, worker, ejecutar, segundos_lease=segundos_lease,
                        max_intentos=max_intentos, pasar_token=True)
