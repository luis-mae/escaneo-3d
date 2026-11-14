"""Motor transaccional de cuotas FREE/PLUS/PRO para el backend ESCANEO 3D.

Este módulo prepara el control de consumo del backend autenticado. No procesa
pagos ni autentica usuarios; user_id debe provenir de una identidad verificada.
Las cuotas son valores iniciales configurables, no precios ni oferta comercial.
"""
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

CUOTAS_INICIALES = {"FREE": 5, "PLUS": 25, "PRO": 50}
PLANES_VALIDOS = frozenset(CUOTAS_INICIALES)


def _ruta_db():
    return Path(os.environ.get("ESCANEO3D_BILLING_DB", "datos_escaneo/entitlements.sqlite3"))


def _conectar():
    ruta = _ruta_db()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(ruta, timeout=15, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("PRAGMA busy_timeout = 15000")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS accounts (
            user_id TEXT PRIMARY KEY,
            plan TEXT NOT NULL CHECK(plan IN ('FREE','PLUS','PRO')),
            active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS usage_events (
            user_id TEXT NOT NULL REFERENCES accounts(user_id) ON DELETE CASCADE,
            event_id TEXT NOT NULL,
            period TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('reserved','consumed','released')),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY(user_id, event_id)
        );
        CREATE INDEX IF NOT EXISTS idx_usage_period ON usage_events(user_id, period, status);
    """)
    return db


def configurar_cuenta(user_id, plan="FREE", active=True):
    if not isinstance(user_id, str) or not user_id.strip() or len(user_id) > 200:
        raise ValueError("user_id inválido")
    if not isinstance(plan, str):
        raise ValueError("Plan inválido")
    plan = plan.upper()
    if type(active) is not bool:
        raise ValueError("Estado de cuenta inválido")
    if plan not in PLANES_VALIDOS:
        raise ValueError("Plan inválido")
    ahora = datetime.now(timezone.utc).isoformat()
    with closing(_conectar()) as db:
        db.execute("""INSERT INTO accounts(user_id, plan, active, updated_at)
                      VALUES(?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET
                      plan=excluded.plan, active=excluded.active, updated_at=excluded.updated_at""",
                   (user_id.strip(), plan, int(bool(active)), ahora))
    return obtener_entitlements(user_id.strip())


def _periodo_actual():
    return datetime.now(timezone.utc).strftime("%Y-%m")


def obtener_entitlements(user_id):
    with closing(_conectar()) as db:
        cuenta = db.execute("SELECT * FROM accounts WHERE user_id=?", (user_id,)).fetchone()
        if cuenta is None:
            raise KeyError("Cuenta no encontrada")
        plan = cuenta["plan"]
        periodo = _periodo_actual()
        usados = db.execute("""SELECT COUNT(*) FROM usage_events
                               WHERE user_id=? AND period=? AND status IN ('reserved','consumed')""",
                            (user_id, periodo)).fetchone()[0]
        limite = CUOTAS_INICIALES[plan]
        return {
            "plan": plan, "activo": bool(cuenta["active"]),
            "periodo_utc": periodo, "cuota_mensual": limite,
            "consumidos_o_reservados": usados, "disponibles": max(0, limite-usados),
            "capacidades": {
                "reconstruccion_local": True,
                "procesamiento_remoto": bool(cuenta["active"]),
                "reconstruccion_densa_remota": plan == "PRO" and bool(cuenta["active"]),
                "exportacion": True,
            },
            "nota": "Cuotas preliminares; no implica suscripción ni pago activo.",
        }


def reservar_trabajo(user_id, event_id):
    if not isinstance(event_id, str) or not event_id.strip() or len(event_id) > 200:
        raise ValueError("event_id inválido")
    ahora = datetime.now(timezone.utc).isoformat()
    periodo = _periodo_actual()
    db = _conectar()
    try:
        db.execute("BEGIN IMMEDIATE")
        cuenta = db.execute("SELECT plan, active FROM accounts WHERE user_id=?", (user_id,)).fetchone()
        if cuenta is None or not cuenta["active"]:
            raise PermissionError("Cuenta inexistente o inactiva")
        existente = db.execute("SELECT * FROM usage_events WHERE user_id=? AND event_id=?",
                               (user_id, event_id)).fetchone()
        if existente:
            if existente["status"] == "released":
                raise ValueError("El identificador de trabajo ya fue liberado; usá uno nuevo")
            db.commit()
            return {"reservado": True, "repetido": True, "periodo_utc": existente["period"]}
        limite = CUOTAS_INICIALES[cuenta["plan"]]
        usados = db.execute("""SELECT COUNT(*) FROM usage_events
                               WHERE user_id=? AND period=? AND status IN ('reserved','consumed')""",
                            (user_id, periodo)).fetchone()[0]
        if usados >= limite:
            raise PermissionError("Cuota mensual agotada")
        db.execute("""INSERT INTO usage_events(user_id,event_id,period,status,created_at,updated_at)
                      VALUES(?,?,?,'reserved',?,?)""", (user_id, event_id, periodo, ahora, ahora))
        db.commit()
        return {"reservado": True, "repetido": False, "periodo_utc": periodo,
                "cuota_restante": limite-usados-1}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def finalizar_trabajo(user_id, event_id, exito=True):
    ahora = datetime.now(timezone.utc).isoformat()
    nuevo_estado = "consumed" if exito else "released"
    with closing(_conectar()) as db:
        cursor = db.execute("""UPDATE usage_events SET status=?, updated_at=?
                               WHERE user_id=? AND event_id=? AND status='reserved'""",
                            (nuevo_estado, ahora, user_id, event_id))
        if cursor.rowcount != 1:
            raise ValueError("No existe una reserva activa para ese trabajo")
    return {"estado": nuevo_estado, "event_id": event_id}



def eliminar_cuenta(user_id):
    """Elimina cuenta y eventos de cuota asociados; las carpetas se borran en la capa API."""
    db = _conectar()
    try:
        db.execute("BEGIN IMMEDIATE")
        cursor = db.execute("DELETE FROM accounts WHERE user_id=?", (user_id,))
        if cursor.rowcount != 1:
            raise KeyError("Cuenta no encontrada")
        db.commit()
        return {"eliminada": True, "user_id": user_id}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
