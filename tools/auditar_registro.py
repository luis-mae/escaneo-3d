"""Auditoría geométrica de registro de nubes sin alterar originales.

Calcula distancias bidireccionales de vecino más próximo y cobertura a un
umbral dado. Las métricas son diagnósticas, no prueban correspondencia física.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree


def auditar_registro(origen, destino, transformacion, umbral, cobertura_minima=0.6):
    a = np.asarray(origen, dtype=float)
    b = np.asarray(destino, dtype=float)
    for p in (a, b):
        if p.ndim != 2 or p.shape[1] != 3 or not len(p) or not np.isfinite(p).all():
            raise ValueError("Nube Nx3 no vacía y finita requerida")
    if not np.isfinite(umbral) or umbral <= 0:
        raise ValueError("Umbral inválido")
    if not np.isfinite(cobertura_minima) or not 0 <= cobertura_minima <= 1:
        raise ValueError("Cobertura mínima inválida")
    if not isinstance(transformacion, dict):
        raise ValueError("Transformación inválida")
    try:
        escala = float(transformacion["escala"])
        r = np.asarray(transformacion["rotacion"], dtype=float)
        t = np.asarray(transformacion["traslacion"], dtype=float)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Transformación incompleta") from exc
    if (not np.isfinite(escala) or escala <= 0 or r.shape != (3, 3)
            or t.shape != (3,) or not np.isfinite(r).all() or not np.isfinite(t).all()
            or not np.allclose(r.T @ r, np.eye(3), atol=1e-5)
            or not np.isclose(np.linalg.det(r), 1.0, atol=1e-5)):
        raise ValueError("Transformación no es una similitud válida")
    a_reg = escala * (a @ r.T) + t
    d_ab = cKDTree(b).query(a_reg, k=1)[0]
    d_ba = cKDTree(a_reg).query(b, k=1)[0]
    ca, cb = float(np.mean(d_ab <= umbral)), float(np.mean(d_ba <= umbral))
    cobertura = min(ca, cb)
    return {
        "estado": "cobertura_suficiente" if cobertura >= cobertura_minima else "cobertura_insuficiente",
        "cobertura_origen": ca,
        "cobertura_destino": cb,
        "cobertura_bidireccional": cobertura,
        "rmse_origen": float(np.sqrt(np.mean(d_ab ** 2))),
        "rmse_destino": float(np.sqrt(np.mean(d_ba ** 2))),
        "percentil95_origen": float(np.percentile(d_ab, 95)),
        "percentil95_destino": float(np.percentile(d_ba, 95)),
        "umbral": float(umbral),
        "cobertura_minima": float(cobertura_minima),
        "advertencia": "Las distancias de vecinos próximos no certifican geometría, homología, escala métrica ni precisión de impresión."
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("entrada", type=Path, help="JSON con origen, destino y transformacion")
    p.add_argument("--salida", type=Path, required=True)
    p.add_argument("--umbral", type=float, required=True)
    p.add_argument("--cobertura-minima", type=float, default=0.6)
    args = p.parse_args()
    data = json.loads(args.entrada.read_text(encoding="utf-8"))
    result = auditar_registro(data["origen"], data["destino"], data["transformacion"],
                             args.umbral, args.cobertura_minima)
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
