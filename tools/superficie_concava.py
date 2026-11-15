"""Superficie alpha 3D experimental desde puntos; no garantiza malla cerrada.

Filtra tetraedros de Delaunay por radio de circunsfera y extrae caras
fronterizas. El parámetro alpha está en unidades de la nube de entrada.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.spatial import Delaunay, QhullError

try:
    from .superficie_nube import guardar_obj
except ImportError:
    from superficie_nube import guardar_obj


def superficie_alpha(puntos, alpha):
    p = np.asarray(puntos, dtype=float)
    if p.ndim != 2 or p.shape[1] != 3 or len(p) < 4 or not np.isfinite(p).all():
        raise ValueError('Se requieren al menos cuatro puntos 3D finitos')
    if not np.isfinite(alpha) or alpha <= 0:
        raise ValueError('alpha debe ser un número positivo finito')
    p = np.unique(p, axis=0)
    if len(p) < 4:
        raise ValueError('Se requieren cuatro puntos 3D distintos')
    try:
        tetra = Delaunay(p).simplices
    except QhullError as exc:
        raise ValueError('La nube no define un volumen 3D') from exc
    fronteras = Counter()
    orientaciones = {}
    aceptados = 0
    # Resolver radios por bloques para evitar miles de llamadas Python a linalg.solve.
    # La memoria temporal se mantiene acotada incluso con nubes grandes.
    for inicio in range(0, len(tetra), 4096):
        bloque = tetra[inicio:inicio + 4096]
        coords = p[bloque]
        a = coords[:, 0, :]
        vectores = coords[:, 1:, :] - a[:, None, :]
        matrices = 2.0 * vectores
        # Sistema trasladado al primer vértice: reduce cancelación numérica
        # cuando COLMAP produce coordenadas con desplazamiento grande.
        rhs = np.sum(vectores ** 2, axis=2)
        determinantes = np.linalg.det(matrices)
        escala = np.maximum(np.max(np.abs(matrices), axis=(1, 2)), 1e-15)
        validos = np.isfinite(determinantes) & (np.abs(determinantes) > 1e-12 * escala ** 3)
        if not np.any(validos):
            continue
        indices_validos = np.flatnonzero(validos)
        try:
            centros = np.linalg.solve(matrices[validos], rhs[validos])
        except np.linalg.LinAlgError:
            # Resolver singularidades residuales individualmente sin perder el bloque.
            centros = np.full((len(indices_validos), 3), np.nan)
            for j, idx in enumerate(indices_validos):
                try:
                    centros[j] = np.linalg.solve(matrices[idx], rhs[idx])
                except np.linalg.LinAlgError:
                    continue
        radios = np.linalg.norm(centros, axis=1)
        elegidos = indices_validos[np.isfinite(radios) & (radios <= alpha)]
        aceptados += len(elegidos)
        for ids in bloque[elegidos]:
            for excluido in range(4):
                face = [int(ids[j]) for j in range(4) if j != excluido]
                v0, v1, v2 = p[face]
                opuesto = p[int(ids[excluido])]
                if np.dot(np.cross(v1-v0, v2-v0), opuesto-v0) > 0:
                    face[1], face[2] = face[2], face[1]
                key = tuple(sorted(face))
                fronteras[key] += 1
                orientaciones[key] = face
    caras = np.asarray([orientaciones[k] for k, count in fronteras.items() if count == 1], dtype=int).reshape(-1, 3)
    return p, caras, aceptados


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('entrada', type=Path, help='JSON con puntos [[x,y,z],...]')
    parser.add_argument('--alpha', type=float, required=True, help='Radio máximo de circunsfera en unidades de entrada')
    parser.add_argument('--salida', type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.entrada.read_text(encoding='utf-8'))
    vertices, caras, n = superficie_alpha(data['puntos'], args.alpha)
    if not len(caras):
        raise SystemExit('Ningún tetraedro aceptado: aumentá alpha o mejorá la nube')
    guardar_obj(args.salida, vertices, caras)
    print(json.dumps({'vertices': len(vertices), 'caras': len(caras), 'tetraedros_aceptados': n,
                      'advertencia': 'Alpha shape experimental; no garantiza superficie cerrada, orientación global ni escala real.'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
