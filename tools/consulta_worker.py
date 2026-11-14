"""Consulta segura de trabajos experimentales, sin alterar el servidor actual.

Esta capa es de solo lectura: no arranca workers ni concede permisos.
"""
import re
import sqlite3
from pathlib import Path


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
    # No inicializar ni migrar esquemas al consultar: lectura estricta.
    try:
        # URI construida desde Path.as_uri evita que caracteres especiales
        # del directorio se interpreten como parámetros SQLite.
        uri = ruta.as_uri() + "?mode=ro"
        with sqlite3.connect(uri, uri=True, timeout=5) as db:
            fila = db.execute(
                "SELECT estado,intentos FROM trabajos WHERE id=? AND propietario=?",
                (identificador, propietario),
            ).fetchone()
    except sqlite3.Error:
        return None
    return {"estado": fila[0], "intentos": fila[1]} if fila else None
