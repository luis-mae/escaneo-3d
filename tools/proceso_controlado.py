"""Ejecución de subprocesos COLMAP con timeout y cancelación cooperativa."""
import subprocess
import time


class ProcesoCancelado(RuntimeError):
    """El usuario solicitó cancelar el trabajo en ejecución."""


def ejecutar_comando(comando, timeout_segundos, cancel_event=None):
    if not isinstance(timeout_segundos, (int, float)) or timeout_segundos <= 0:
        raise ValueError("Timeout inválido")
    if cancel_event is None:
        return subprocess.run(
            comando, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout_segundos, check=False,
        )
    proceso = subprocess.Popen(
        comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace",
    )
    inicio = time.monotonic()
    while True:
        if cancel_event is not None and cancel_event.is_set():
            proceso.terminate()
            try:
                proceso.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                proceso.kill()
                proceso.communicate()
            raise ProcesoCancelado("Trabajo cancelado por solicitud del usuario")
        restante = timeout_segundos - (time.monotonic() - inicio)
        if restante <= 0:
            proceso.kill()
            salida, error = proceso.communicate()
            raise subprocess.TimeoutExpired(
                comando, timeout_segundos, output=salida, stderr=error
            )
        try:
            salida, error = proceso.communicate(timeout=min(0.2, restante))
            return subprocess.CompletedProcess(comando, proceso.returncode, salida, error)
        except subprocess.TimeoutExpired:
            continue
