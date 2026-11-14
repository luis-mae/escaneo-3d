#!/usr/bin/env python3
"""Mediciones geométricas STL con unidades explícitas y advertencias de fiabilidad."""
import argparse
from collections import Counter
import json
import math
from verificar_stl import leer_stl


def medir(caras, unidad='mm'):
    if unidad not in ('mm', 'cm', 'm', 'in'):
        raise ValueError('Unidad no admitida')
    caras = list(caras)
    if not caras:
        raise ValueError('Malla vacía')
    factor = {'mm': 1, 'cm': 10, 'm': 1000, 'in': 25.4}[unidad]
    minimo = [math.inf]*3; maximo = [-math.inf]*3
    area = volumen6 = 0.0
    edges = Counter(); directions = Counter(); degenerados = 0
    for tri in caras:
        if len(tri) != 3 or any(len(p) != 3 or not all(math.isfinite(x) for x in p) for p in tri):
            raise ValueError('Triángulo inválido')
        a,b,c = tri
        for p in tri:
            for k in range(3):
                minimo[k] = min(minimo[k], p[k]); maximo[k] = max(maximo[k], p[k])
        u = [b[k]-a[k] for k in range(3)]; v = [c[k]-a[k] for k in range(3)]
        cross = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
        norma = math.sqrt(sum(x*x for x in cross))
        area += norma/2
        if norma < 1e-10: degenerados += 1
        volumen6 += sum(a[k]*cross[k] for k in range(3))
        for p,q in ((a,b),(b,c),(c,a)):
            edge = tuple(sorted((p,q)))
            edges[edge] += 1
            directions[(p,q)] += 1
    abiertas = sum(v==1 for v in edges.values())
    no_manifold = sum(v>2 for v in edges.values())
    inconsistentes = sum(v==2 and directions.get(edge,0)!=1 for edge,v in edges.items())
    confiable = abiertas==0 and no_manifold==0 and degenerados==0 and inconsistentes==0
    return {
        'unidad_declarada_por_usuario': unidad,
        'dimensiones_mm': [round((maximo[k]-minimo[k])*factor,5) for k in range(3)],
        'area_superficial_mm2': round(area*factor**2,5),
        'volumen_mm3': round(abs(volumen6)/6*factor**3,5) if confiable else None,
        'volumen_estimado_valido_topologicamente': confiable,
        'triangulos': len(caras), 'triangulos_degenerados': degenerados,
        'aristas_abiertas': abiertas, 'aristas_no_manifold': no_manifold,
        'aristas_con_orientacion_inconsistente': inconsistentes,
        'advertencia': 'STL no contiene unidades. La topología cerrada no garantiza ausencia de autointersecciones ni exactitud del escaneo.'
    }

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archivo'); parser.add_argument('--unidad', choices=['mm','cm','m','in'], required=True)
    args=parser.parse_args()
    print(json.dumps(medir(leer_stl(args.archivo),args.unidad),ensure_ascii=False,indent=2))
