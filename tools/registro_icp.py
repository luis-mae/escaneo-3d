"""Registro ICP conservador de dos nubes prealineadas.

Reestima correspondencias mutuas y una transformación rígida (escala fija)
en iteraciones. Rechaza falta de solapamiento. No resuelve registro global.
"""
import argparse
import json
from pathlib import Path

import numpy as np

try:
    from .correspondencias_3d import correspondencias_mutuas
    from .registrar_escala import estimar_similitud
except ImportError:
    from correspondencias_3d import correspondencias_mutuas
    from registrar_escala import estimar_similitud


def registrar_icp(origen, destino, radio, max_iter=30, tolerancia=1e-7, minimo=3):
    """Transforma origen hacia destino; mantiene escala exactamente en 1."""
    a, b = np.asarray(origen, dtype=float), np.asarray(destino, dtype=float)
    for pts in (a, b):
        if pts.ndim != 2 or pts.shape[1] != 3 or len(pts) < 3 or not np.isfinite(pts).all():
            raise ValueError("Nube Nx3 inválida")
    if not np.isfinite(radio) or radio <= 0:
        raise ValueError("Radio inválido")
    if isinstance(max_iter, bool) or not isinstance(max_iter, int) or max_iter < 1:
        raise ValueError("max_iter inválido")
    if not np.isfinite(tolerancia) or tolerancia < 0:
        raise ValueError("Tolerancia inválida")
    rotacion, traslacion = np.eye(3), np.zeros(3)
    anterior = float("inf")
    historial = []
    for _ in range(max_iter):
        actual = a @ rotacion.T + traslacion
        pares = correspondencias_mutuas(actual, b, radio, minimo=minimo)
        x, y = np.asarray(pares["origen"]), np.asarray(pares["destino"])
        # Estimación rígida Kabsch: NO permitir escala libre de Sim(3).
        xm, ym = x.mean(axis=0), y.mean(axis=0)
        ac, bc = x - xm, y - ym
        if np.linalg.matrix_rank(ac, tol=1e-10) < 2:
            raise ValueError("Correspondencias degeneradas")
        u, _, vt = np.linalg.svd(bc.T @ ac)
        correction = np.eye(3)
        correction[2, 2] = np.sign(np.linalg.det(u @ vt))
        r = u @ correction @ vt
        t = ym - r @ xm
        nueva_rotacion = r @ rotacion
        nueva_traslacion = r @ traslacion + t
        residuo = np.linalg.norm((x @ r.T + t) - y, axis=1)
        rmse = float(np.sqrt(np.mean(residuo ** 2)))
        historial.append({"pares": pares["cantidad"], "rmse": rmse})
        rotacion, traslacion = nueva_rotacion, nueva_traslacion
        if abs(anterior - rmse) <= tolerancia:
            break
        anterior = rmse
    return {
        "escala": 1.0,
        "rotacion": rotacion.tolist(),
        "traslacion": traslacion.tolist(),
        "iteraciones": len(historial),
        "historial": historial,
        "estado": "registro_rigido_local_experimental",
        "advertencia": "Requiere prealineación y solapamiento. Mínimo local; no garantiza registro correcto ni escala métrica."
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("entrada", type=Path)
    p.add_argument("--salida", type=Path, required=True)
    p.add_argument("--radio", type=float, required=True)
    p.add_argument("--iteraciones", type=int, default=30)
    args = p.parse_args()
    data = json.loads(args.entrada.read_text(encoding="utf-8"))
    resultado = registrar_icp(data["origen"], data["destino"], args.radio, args.iteraciones)
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
