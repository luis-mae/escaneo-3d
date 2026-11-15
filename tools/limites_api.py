"""Límite conservador por IP de origen directo, por proceso.

No confía en X-Forwarded-For: configurar proxy de confianza y un límite
adicional en el gateway. El estado no se comparte entre réplicas.
"""
import threading
import time
from collections import deque

_LOCK = threading.Lock()
_BUCKETS = {}
_MAX_CLIENTES = 10000


def permitir(ip, ruta, metodo, ahora=None):
    """Devuelve (permitido, segundos_para_reintentar)."""
    if metodo not in ("POST", "PATCH", "PUT", "DELETE") or not ruta.startswith("/api/"):
        return True, 0
    if ruta == "/api/proyectos" and metodo == "POST":
        limite, ventana, categoria = 4, 3600, "subidas"
    else:
        limite, ventana, categoria = 60, 60, "mutaciones"
    instante = time.monotonic() if ahora is None else float(ahora)
    clave = (str(ip)[:128], categoria)
    with _LOCK:
        if len(_BUCKETS) >= _MAX_CLIENTES:
            for k, valores in list(_BUCKETS.items()):
                if not valores or valores[-1] <= instante - 3600:
                    del _BUCKETS[k]
            if len(_BUCKETS) >= _MAX_CLIENTES and clave not in _BUCKETS:
                return False, 60
        marcas = _BUCKETS.setdefault(clave, deque())
        while marcas and marcas[0] <= instante - ventana:
            marcas.popleft()
        if len(marcas) >= limite:
            return False, max(1, int(marcas[0] + ventana - instante + 0.999))
        marcas.append(instante)
        return True, 0
