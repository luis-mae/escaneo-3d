"""Alineación Sim(3) de dos reconstrucciones mediante puntos 3D compartidos.

No estima puntos compartidos desde fotos ni resuelve bundle adjustment.
"""
import argparse
import json
from pathlib import Path
import numpy as np


def estimar_similitud(origen, destino):
    """Encuentra escala s>0, rotación R y traslación t: destino ~= s*origen@R.T+t."""
    a = np.asarray(origen, dtype=float)
    b = np.asarray(destino, dtype=float)
    if a.ndim != 2 or a.shape[1] != 3 or a.shape != b.shape or len(a) < 3:
        raise ValueError('Se requieren al menos tres correspondencias 3D')
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Coordenadas no finitas')
    am, bm = a.mean(axis=0), b.mean(axis=0)
    ac, bc = a-am, b-bm
    if np.linalg.matrix_rank(ac, tol=1e-9) < 2 or np.linalg.matrix_rank(bc, tol=1e-9) < 2:
        raise ValueError('Correspondencias degeneradas o colineales')
    u, singular, vt = np.linalg.svd(bc.T @ ac)
    correction = np.eye(3)
    correction[-1, -1] = np.sign(np.linalg.det(u @ vt))
    R = u @ correction @ vt
    denom = np.sum(ac**2)
    s = float(np.sum(singular * np.diag(correction)) / denom)
    if not np.isfinite(s) or s <= 1e-12:
        raise ValueError('Escala inválida')
    t = bm - s * (R @ am)
    predicted = s * (a @ R.T) + t
    errors = np.linalg.norm(predicted-b, axis=1)
    return {'escala': s, 'rotacion': R.tolist(), 'traslacion': t.tolist(),
            'rmse': float(np.sqrt(np.mean(errors**2))), 'error_max': float(errors.max()),
            'puntos': len(a), 'estado': 'alineacion_por_referencias'}


def transformar_puntos(puntos, transformacion):
    pts = np.asarray(puntos, dtype=float)
    if pts.ndim != 2 or pts.shape[1] != 3 or not np.isfinite(pts).all():
        raise ValueError('Nube inválida')
    return transformacion['escala'] * (pts @ np.asarray(transformacion['rotacion']).T) + np.asarray(transformacion['traslacion'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('correspondencias', type=Path, help='JSON con origen y destino: listas Nx3')
    parser.add_argument('--salida', type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.correspondencias.read_text(encoding='utf-8'))
    result = estimar_similitud(data['origen'], data['destino'])
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(f"RMSE: {result['rmse']:.6g} | escala: {result['escala']:.6g}")


if __name__ == '__main__':
    main()
