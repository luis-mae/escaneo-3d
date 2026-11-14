#!/usr/bin/env python3
"""Auditoría geométrica de STL ASCII/binario, sin dependencias externas."""
import argparse
import json
import math
import struct
from collections import Counter
from pathlib import Path


def leer_stl(path):
    data = Path(path).read_bytes()
    if len(data) >= 84:
        n = struct.unpack_from('<I', data, 80)[0]
        if 84 + n * 50 == len(data):
            for i in range(n):
                values = struct.unpack_from('<12fH', data, 84 + i * 50)
                yield tuple(tuple(values[j:j+3]) for j in (3, 6, 9))
            return
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ValueError('STL binario inválido') from exc
    vertices = []
    for line in text.splitlines():
        parts = line.strip().split()
        if len(parts) == 4 and parts[0].lower() == 'vertex':
            vertices.append(tuple(float(v) for v in parts[1:]))
            if len(vertices) == 3:
                yield tuple(vertices)
                vertices = []
    if vertices:
        raise ValueError('STL ASCII incompleto')


def analizar(path):
    bounds_min = [math.inf] * 3
    bounds_max = [-math.inf] * 3
    edges = Counter()
    triangles = degenerates = 0
    for face in leer_stl(path):
        triangles += 1
        if any(not math.isfinite(v) for p in face for v in p):
            raise ValueError('Coordenadas no finitas en la malla')
        for p in face:
            for i, v in enumerate(p):
                bounds_min[i] = min(bounds_min[i], v)
                bounds_max[i] = max(bounds_max[i], v)
        a, b, c = face
        u = [b[i] - a[i] for i in range(3)]
        v = [c[i] - a[i] for i in range(3)]
        cross = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
        if sum(x*x for x in cross) < 1e-20:
            degenerates += 1
        for p, q in ((a,b),(b,c),(c,a)):
            edges[tuple(sorted((p,q)))] += 1
    if not triangles:
        raise ValueError('No se encontraron triángulos')
    open_edges = sum(count == 1 for count in edges.values())
    nonmanifold = sum(count > 2 for count in edges.values())
    return {'archivo': str(path), 'triangulos': triangles, 'triangulos_degenerados': degenerates,
            'aristas_abiertas': open_edges, 'aristas_no_manifold': nonmanifold,
            'dimensiones_unidades_archivo': [round(bounds_max[i]-bounds_min[i], 6) for i in range(3)],
            'malla_cerrada_por_aristas': open_edges == 0 and nonmanifold == 0 and degenerates == 0,
            'advertencia': 'STL no contiene unidades ni garantiza exactitud dimensional; verificar escala y medidas físicas.'}


def main():
    parser = argparse.ArgumentParser(description='Verificar STL antes de imprimir')
    parser.add_argument('archivo')
    args = parser.parse_args()
    print(json.dumps(analizar(args.archivo), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
