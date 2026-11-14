"""Cola SQLite local persistente para futuros workers; no sustituye la cola actual.

No ejecutar jobs directamente desde este módulo. La integración con COLMAP,
aislamiento por usuario y despliegue remoto requieren validación separada.
"""
import sqlite3
import time
import uuid
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS trabajos (
 id TEXT PRIMARY KEY,
 propietario TEXT NOT NULL,
 estado TEXT NOT NULL CHECK (estado IN ('pendiente','ejecutando','completado','fallido','cancelado')),
 creado REAL NOT NULL,
 actualizado REAL NOT NULL,
 intentos INTEGER NOT NULL DEFAULT 0,
 worker TEXT,
 lease_hasta REAL,
 error_codigo TEXT,
 token_lease TEXT
);
CREATE INDEX IF NOT EXISTS idx_trabajos_estado ON trabajos(estado, creado);
"""


class ColaPersistente:
    def __init__(self, ruta):
        self.ruta = Path(ruta)
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        with self._conexion() as db:
            db.executescript(SCHEMA)
            columnas = {fila[1] for fila in db.execute('PRAGMA table_info(trabajos)')}
            if 'token_lease' not in columnas:
                db.execute('ALTER TABLE trabajos ADD COLUMN token_lease TEXT')

    def _conexion(self):
        db = sqlite3.connect(self.ruta, timeout=10, isolation_level=None)
        db.execute("PRAGMA busy_timeout=10000")
        return db

    def agregar(self, id_trabajo, propietario):
        if not id_trabajo or not propietario:
            raise ValueError("ID y propietario obligatorios")
        ahora = time.time()
        with self._conexion() as db:
            cursor = db.execute(
                "INSERT OR IGNORE INTO trabajos(id,propietario,estado,creado,actualizado) VALUES(?,?,'pendiente',?,?)",
                (id_trabajo, propietario, ahora, ahora))
            return cursor.rowcount == 1

    def reclamar(self, worker, segundos_lease=300, max_intentos=3):
        reclamo = self.reclamar_con_token(worker, segundos_lease, max_intentos)
        return reclamo[0] if reclamo else None

    def reclamar_con_token(self, worker, segundos_lease=300, max_intentos=3):
        if not worker or segundos_lease <= 0 or max_intentos < 1:
            raise ValueError("Worker, lease o intentos inválidos")
        ahora = time.time()
        token = uuid.uuid4().hex
        with self._conexion() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                fila = db.execute(
                    """SELECT id FROM trabajos WHERE
                    (estado='pendiente' OR (estado='ejecutando' AND lease_hasta < ?))
                    AND intentos < ? ORDER BY creado,id LIMIT 1""",
                    (ahora, max_intentos)).fetchone()
                if fila is None:
                    db.execute("COMMIT")
                    return None
                db.execute(
                    """UPDATE trabajos SET estado='ejecutando', intentos=intentos+1,
                    worker=?, token_lease=?, lease_hasta=?, actualizado=? WHERE id=?""",
                    (worker, token, ahora + segundos_lease, ahora, fila[0]))
                db.execute("COMMIT")
                return fila[0], token
            except BaseException:
                db.execute("ROLLBACK")
                raise

    def renovar(self, id_trabajo, worker, segundos_lease=300, token_lease=None):
        if segundos_lease <= 0:
            raise ValueError("Lease inválido")
        ahora = time.time()
        if not token_lease:
            return False
        with self._conexion() as db:
            cursor = db.execute(
                """UPDATE trabajos SET lease_hasta=?, actualizado=?
                WHERE id=? AND worker=? AND token_lease=? AND estado='ejecutando' AND lease_hasta>?""",
                (ahora + segundos_lease, ahora, id_trabajo, worker, token_lease, ahora))
            return cursor.rowcount == 1

    def finalizar(self, id_trabajo, worker, exito, token_lease=None):
        if not token_lease:
            return False
        ahora = time.time()
        with self._conexion() as db:
            cursor = db.execute(
                """UPDATE trabajos SET estado=?, actualizado=?, lease_hasta=NULL, token_lease=NULL
                WHERE id=? AND worker=? AND token_lease=? AND estado='ejecutando' AND lease_hasta>?""",
                ("completado" if exito else "fallido", ahora, id_trabajo, worker, token_lease, ahora))
            return cursor.rowcount == 1

    def token_actual(self, id_trabajo, worker):
        """Solo para el worker reclamante; no exponer por HTTP."""
        ahora = time.time()
        with self._conexion() as db:
            fila = db.execute(
                "SELECT token_lease FROM trabajos WHERE id=? AND worker=? AND estado='ejecutando' AND lease_hasta>?",
                (id_trabajo, worker, ahora)).fetchone()
        return fila[0] if fila else None

    def agotar_vencidos(self, max_intentos=3):
        """Marca fallidos los trabajos agotados cuyo lease ya venció."""
        if max_intentos < 1:
            raise ValueError('Máximo de intentos inválido')
        ahora = time.time()
        with self._conexion() as db:
            cursor = db.execute(
                """UPDATE trabajos SET estado='fallido', error_codigo='INTENTOS_AGOTADOS',
                actualizado=?, lease_hasta=NULL, token_lease=NULL
                WHERE estado='ejecutando' AND lease_hasta<? AND intentos>=?""",
                (ahora, ahora, max_intentos))
            return cursor.rowcount

    def fallidos_por_agotamiento(self):
        """Devuelve IDs y propietarios para reconciliar cuotas fuera de la transacción."""
        with self._conexion() as db:
            return db.execute(
                "SELECT id,propietario FROM trabajos WHERE estado='fallido' AND error_codigo='INTENTOS_AGOTADOS'"
            ).fetchall()

    def estado_reclamo(self, id_trabajo, worker, token_lease):
        """Valida que el reclamante siga teniendo el lease; no garantiza exclusión de procesos."""
        if not token_lease:
            return False
        with self._conexion() as db:
            fila = db.execute(
                """SELECT 1 FROM trabajos WHERE id=? AND worker=? AND token_lease=?
                AND estado='ejecutando' AND lease_hasta>?""",
                (id_trabajo, worker, token_lease, time.time())).fetchone()
        return fila is not None

    def cancelar(self, id_trabajo, propietario):
        ahora = time.time()
        with self._conexion() as db:
            cursor = db.execute(
                """UPDATE trabajos SET estado='cancelado', actualizado=?, lease_hasta=NULL
                WHERE id=? AND propietario=? AND estado='pendiente'""",
                (ahora, id_trabajo, propietario))
            return cursor.rowcount == 1

    def consultar(self, id_trabajo, propietario):
        with self._conexion() as db:
            fila = db.execute(
                "SELECT estado,intentos FROM trabajos WHERE id=? AND propietario=?",
                (id_trabajo, propietario)).fetchone()
        return {"estado": fila[0], "intentos": fila[1]} if fila else None
