"""Orquestación experimental de worker con staging y publicación.

El callback recibe (id_trabajo, carpeta_staging) y debe escribir solo allí.
No conecta COLMAP ni cuotas; no habilitar procesamiento remoto público.
"""
from pathlib import Path

from tools.resultados_aislados import preparar, publicar
from tools.worker_base import ejecutar_uno


def ejecutar_con_resultados(cola, base, worker, procesar, *, segundos_lease=300, max_intentos=3):
    """Ejecuta un trabajo aislando archivos por token; exige worker exclusivo."""
    def ejecutar(id_trabajo):
        token = cola.token_actual(id_trabajo, worker)
        if token is None:
            raise RuntimeError("Lease perdido antes de preparar resultados")
        carpeta = preparar(base, id_trabajo, token)
        procesar(id_trabajo, Path(carpeta))
        publicar(base, id_trabajo, worker, token, cola)
    return ejecutar_uno(cola, worker, ejecutar, segundos_lease=segundos_lease,
                        max_intentos=max_intentos)
