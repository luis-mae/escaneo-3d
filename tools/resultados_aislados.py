"""Staging por ejecución para evitar que un lease viejo sobrescriba resultados.

Solo habilita promoción si el lease sigue vigente. Para despliegues remotos
se necesita además aislamiento de procesos, almacenamiento compartido y
protocolo de publicación con recuperación ante caídas.
"""
import os
import re
from pathlib import Path

ID_RE = re.compile(r"^[a-f0-9]{32}$")


class PublicacionRechazada(RuntimeError):
    pass


def _identificador(valor):
    if not isinstance(valor, str) or not ID_RE.fullmatch(valor):
        raise ValueError("Identificador inválido")
    return valor


def preparar(base, id_trabajo, token):
    id_trabajo = _identificador(id_trabajo)
    token = _identificador(token)
    base = Path(base).resolve()
    destino = base / "temporales" / id_trabajo / token
    destino.mkdir(parents=True, exist_ok=False)
    return destino


def publicar(base, id_trabajo, worker, token, cola, *, nombre="resultado"):
    """Publica una carpeta preparada bajo bloqueo SQLite y lease vigente.

    Requiere que la carpeta de staging y destino estén en el mismo filesystem.
    No sustituye la transacción completa de estados/cuotas del servidor.
    """
    id_trabajo = _identificador(id_trabajo)
    token = _identificador(token)
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", nombre):
        raise ValueError("Nombre inválido")
    base = Path(base).resolve()
    origen = base / "temporales" / id_trabajo / token
    destino = base / "publicados" / id_trabajo / nombre
    if not origen.is_dir() or origen.is_symlink():
        raise FileNotFoundError("No existe staging válido")
    destino.parent.mkdir(parents=True, exist_ok=True)
    # BEGIN IMMEDIATE serializa promociones coordinadas por la misma base SQLite.
    with cola._conexion() as db:
        db.execute("BEGIN IMMEDIATE")
        try:
            import time
            vigente = db.execute(
                """SELECT 1 FROM trabajos WHERE id=? AND worker=? AND token_lease=?
                AND estado='ejecutando' AND lease_hasta>?""",
                (id_trabajo, worker, token, time.time())).fetchone()
            if not vigente:
                raise PublicacionRechazada("Lease inválido o vencido")
            # Revalidar bajo lock: otros workers coordinados no pueden publicar
            # simultáneamente. No sobrescribir incluso si existe un symlink.
            if destino.exists() or destino.is_symlink():
                raise FileExistsError("Resultado ya publicado")
            os.rename(origen, destino)
            db.execute("COMMIT")
        except BaseException:
            db.execute("ROLLBACK")
            raise
    return destino
