"""Ejecutor aislado de callbacks para prototipar workers de la cola persistente.

No ejecuta COLMAP ni publica endpoints. Antes de integrar un pipeline real,
agregar fencing en escrituras de resultados, cuotas y almacenamiento.
"""
import threading
from dataclasses import dataclass

from tools.cola_persistente import ColaPersistente


@dataclass(frozen=True)
class ResultadoWorker:
    id_trabajo: str | None
    estado: str


def ejecutar_uno(cola: ColaPersistente, worker: str, ejecutar, *,
                 segundos_lease: int = 300, max_intentos: int = 3,
                 pasar_cancelacion: bool = False) -> ResultadoWorker:
    """Procesa un callback. Un lease vencido nunca se marca como completado."""
    if segundos_lease < 3:
        raise ValueError("Lease debe durar al menos tres segundos")
    cola.agotar_vencidos(max_intentos=max_intentos)
    reclamo = cola.reclamar_con_token(worker, segundos_lease, max_intentos)
    if reclamo is None:
        return ResultadoWorker(None, "sin_trabajos")
    identificador, token = reclamo
    stop = threading.Event()
    perdido = threading.Event()

    def heartbeat():
        while not stop.wait(segundos_lease / 3):
            if not cola.renovar(identificador, worker, segundos_lease, token_lease=token):
                perdido.set()
                return

    hilo = threading.Thread(target=heartbeat, daemon=True)
    hilo.start()
    try:
        if not cola.estado_reclamo(identificador, worker, token):
            return ResultadoWorker(identificador, "lease_perdido")
        if pasar_cancelacion:
            ejecutar(identificador, perdido)
        else:
            ejecutar(identificador)
        if perdido.is_set() or not cola.finalizar(identificador, worker, True, token_lease=token):
            return ResultadoWorker(identificador, "lease_perdido")
        return ResultadoWorker(identificador, "completado")
    except Exception:
        if perdido.is_set() or not cola.finalizar(identificador, worker, False, token_lease=token):
            return ResultadoWorker(identificador, "lease_perdido")
        return ResultadoWorker(identificador, "fallido")
    finally:
        stop.set()
        hilo.join(timeout=1)
