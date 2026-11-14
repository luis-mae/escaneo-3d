"""Alineación de nubes mediante puntos de control correspondientes.

Requiere al menos tres puntos de control no colineales en cada nube.
La escala relativa se estima, pero no constituye calibración métrica.
"""
import argparse
import json
from pathlib import Path
import numpy as np


def estimar_similitud(origen, destino):
    a, b = np.asarray(origen, dtype=float), np.asarray(destino, dtype=float)
    if a.shape != b.shape or a.ndim != 2 or a.shape[1] != 3 or len(a) < 3:
        raise ValueError('Se necesitan al menos tres correspondencias 3D válidas')
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Coordenadas no finitas')
    ac, bc = a.mean(axis=0), b.mean(axis=0)
    x, y = a - ac, b - bc
    if np.linalg.matrix_rank(x, tol=1e-9) < 2 or np.linalg.matrix_rank(y, tol=1e-9) < 2:
        raise ValueError('Puntos de control colineales o coincidentes')
    u, s, vt = np.linalg.svd(x.T @ y)
    correction = np.eye(3)
    correction[-1, -1] = np.linalg.det(u @ vt)
    rotation = u @ correction @ vt
    scale = float(np.sum(s * np.diag(correction)) / np.sum(x*x))
    if scale <= 0 or not np.isfinite(scale):
        raise ValueError('Escala inválida')
    translation = bc - scale * (ac @ rotation)
    residuals = np.linalg.norm(scale * (a @ rotation) + translation - b, axis=1)
    return {'escala': scale, 'rotacion': rotation.tolist(),
            'traslacion': translation.tolist(), 'error_rms': float(np.sqrt(np.mean(residuals**2))),
            'advertencia': 'Alineación relativa experimental; no valida precisión dimensional.'}


def transformar(puntos, ajuste):
    p = np.asarray(puntos, dtype=float)
    return ajuste['escala'] * (p @ np.asarray(ajuste['rotacion'])) + np.asarray(ajuste['traslacion'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('correspondencias', type=Path, help='JSON con origen y destino, listas Nx3')
    parser.add_argument('--salida', type=Path, required=True)
    args = parser.parse_args()
    datos = json.loads(args.correspondencias.read_text(encoding='utf-8'))
    resultado = estimar_similitud(datos['origen'], datos['destino'])
    args.salida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(resultado, ensure_ascii=False))

if __name__ == '__main__':
    main()
