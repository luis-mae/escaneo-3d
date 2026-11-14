#!/usr/bin/env python3
"""Diagnóstico conservador de bordes abiertos de una malla triangular.

No repara automáticamente: los agujeros pueden ser características intencionales.
"""
from collections import defaultdict
import json
import argparse


def diagnosticar(caras):
    caras = list(caras)
    edges = defaultdict(list)
    for fi, face in enumerate(caras):
        if len(face) != 3 or len(set(map(tuple, face))) != 3:
            raise ValueError('Cada cara debe contener tres vértices distintos')
        for a, b in ((0, 1), (1, 2), (2, 0)):
            u, v = tuple(face[a]), tuple(face[b])
            edges[tuple(sorted((u, v)))].append((fi, u, v))
    boundary = [inc[0][1:] for inc in edges.values() if len(inc) == 1]
    nonmanifold = sum(len(inc) > 2 for inc in edges.values())
    neighbors = defaultdict(list)
    for u, v in boundary:
        neighbors[u].append(v)
        neighbors[v].append(u)
    branch = [v for v, adj in neighbors.items() if len(adj) != 2]
    seen = set()
    loops = []
    chains = []
    for u, v in boundary:
        e = frozenset((u, v))
        if e in seen:
            continue
        path = [u, v]
        seen.add(e)
        prev, cur = u, v
        while cur != u:
            choices = [w for w in neighbors[cur] if w != prev and frozenset((cur, w)) not in seen]
            if len(choices) != 1:
                break
            nxt = choices[0]
            seen.add(frozenset((cur, nxt)))
            path.append(nxt)
            prev, cur = cur, nxt
        if path[-1] == path[0] and len(path) >= 4:
            loops.append(path[:-1])
        else:
            chains.append(path)
    return {
        'triangulos': len(caras),
        'aristas_abiertas': len(boundary),
        'aristas_no_manifold': nonmanifold,
        'vertices_borde_irregulares': len(branch),
        'bucles_cerrados': len(loops),
        'longitudes_bucles': [len(x) for x in loops],
        'cadenas_o_bordes_ambiguos': len(chains),
        'malla_cerrada_por_aristas': len(boundary) == 0 and nonmanifold == 0 and bool(caras),
        'advertencia': 'Un borde abierto puede ser intencional. No implica que sea seguro taparlo ni que la malla sea imprimible.'
    }


if __name__ == '__main__':
    from verificar_stl import leer_stl
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('archivo_stl')
    args = p.parse_args()
    print(json.dumps(diagnosticar(leer_stl(args.archivo_stl)), ensure_ascii=False, indent=2))
