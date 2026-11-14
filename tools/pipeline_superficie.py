"""Pipeline verificable nube JSON -> superficie OBJ + diagnóstico JSON.

No realiza fotogrametría: requiere puntos 3D ya reconstruidos y escalados.
"""
import argparse
import json
from collections import Counter
from pathlib import Path
import numpy as np
try:
    from .superficie_concava import superficie_alpha
    from .superficie_nube import guardar_obj
except ImportError:
    from superficie_concava import superficie_alpha
    from superficie_nube import guardar_obj


def procesar(puntos, alpha):
    vertices, caras, tetraedros = superficie_alpha(puntos, alpha)
    if len(caras) == 0:
        raise ValueError('No se generaron caras; revisar alpha y densidad')
    edges = Counter(tuple(sorted((int(a), int(b)))) for f in caras for a, b in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])))
    frontera = sum(v == 1 for v in edges.values())
    no_manifold = sum(v > 2 for v in edges.values())
    return vertices, caras, {
        'vertices': int(len(vertices)), 'caras': int(len(caras)),
        'tetraedros_aceptados': int(tetraedros), 'aristas_abiertas': int(frontera),
        'aristas_no_manifold': int(no_manifold),
        'malla_cerrada_por_aristas': frontera == 0 and no_manifold == 0,
        'escala': 'heredada de puntos de entrada; no verificada',
        'apto_para_impresion': False,
        'advertencia': 'Resultado experimental: inspeccionar geometría, orientación, unidades y tolerancias antes de imprimir.'
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('entrada', type=Path)
    p.add_argument('--alpha', type=float, required=True)
    p.add_argument('--salida', type=Path, required=True)
    p.add_argument('--informe', type=Path)
    args = p.parse_args()
    data = json.loads(args.entrada.read_text(encoding='utf8'))
    v, f, report = procesar(data['puntos'], args.alpha)
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    guardar_obj(args.salida, v, f)
    informe = args.informe or args.salida.with_suffix('.informe.json')
    informe.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(report, ensure_ascii=False))

if __name__ == '__main__':
    main()
