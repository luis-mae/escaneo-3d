"""Cola SQLite local persistente para futuros workers; no sustituye la cola actual.

No ejecutar jobs directamente desde este módulo. La integración con COLMAP,
aislamiento por usuario y despliegue remoto requieren validación separada.
"""
import sqlite3
import time
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
 error_codigo TEXT
);
CREATE INDEX IF NOT EXISTS idx_trabajos_estado ON trabajos(estado, creado);
"""


class ColaPersistente:
    def __init__(self, ruta):
        self.ruta = Path(ruta)
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        with self._conexion() as db:
            db.executescript(SCHEMA)

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
        if not worker or segundos_lease <= 0 or max_intentos < 1:
            raise ValueError("Worker, lease o intentos inválidos")
        ahora = time.time()
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
                    worker=?, lease_hasta=?, actualizado=? WHERE id=?""",
                    (worker, ahora + segundos_lease, ahora, fila[0]))
                db.execute("COMMIT")
                return fila[0]
            except BaseException:
                db.execute("ROLLBACK")
                raise

    def renovar(self, id_trabajo, worker, segundos_lease=300):
        if segundos_lease <= 0:
            raise ValueError("Lease inválido")
        ahora = time.time()
        with self._conexion() as db:
            cursor = db.execute(
                """UPDATE trabajos SET lease_hasta=?, actualizado=?
                WHERE id=? AND worker=? AND estado='ejecutando' AND lease_hasta>?""",
                (ahora + segundos_lease, ahora, id_trabajo, worker, ahora))
            return cursor.rowcount == 1

    def finalizar(self, id_trabajo, worker, exito):
        ahora = time.time()
        with self._conexion() as db:
            cursor = db.execute(
                """UPDATE trabajos SET estado=?, actualizado=?, lease_hasta=NULL
                WHERE id=? AND worker=? AND estado='ejecutando' AND lease_hasta>?""",
                ("completado" if exito else "fallido", ahora, id_trabajo, worker, ahora))
            return cursor.rowcount == 1

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
