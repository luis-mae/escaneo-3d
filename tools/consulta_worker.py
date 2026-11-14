"""Consulta segura de trabajos experimentales, sin alterar el servidor actual.

Esta capa es de solo lectura: no arranca workers ni concede permisos.
"""
import re
from pathlib import Path

from tools.cola_persistente import ColaPersistente

ID = re.compile(r"^[a-f0-9]{32}$")


def consultar_trabajo(base, identificador, propietario):
    if not isinstance(identificador, str) or not ID.fullmatch(identificador):
        raise ValueError("Identificador inválido")
    if not isinstance(propietario, str) or not propietario.strip():
        raise ValueError("Propietario obligatorio")
    base = Path(base).resolve()
    ruta = base / "cola.sqlite"
    if not ruta.is_file() or ruta.is_symlink():
        return None
    cola = ColaPersistente(ruta)
    return cola.consultar(identificador, propietario)
