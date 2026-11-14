"""Superficie envolvente convexa preliminar desde nube 3D.

NO recupera concavidades ni equivale a reconstrucción fotogramétrica.
Requiere numpy y scipy en el entorno de procesamiento.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.spatial import ConvexHull, QhullError


def generar_superficie(puntos):
    p = np.asarray(puntos, dtype=float)
    if p.ndim != 2 or p.shape[1] != 3 or len(p) < 4 or not np.isfinite(p).all():
        raise ValueError('Se requieren al menos cuatro puntos 3D finitos')
    p = np.unique(p, axis=0)
    if len(p) < 4:
        raise ValueError('Se requieren cuatro puntos distintos')
    try:
        hull = ConvexHull(p)
    except QhullError as exc:
        raise ValueError('Los puntos no definen un volumen tridimensional') from exc
    # scipy devuelve caras, pero no garantiza su orientación para exportación.
    caras = hull.simplices.copy()
    for i, (a, b, c) in enumerate(caras):
        normal = np.cross(p[b] - p[a], p[c] - p[a])
        if np.dot(normal, hull.equations[i, :3]) < 0:
            caras[i] = [a, c, b]
    return p, caras, float(hull.volume)


def guardar_obj(ruta, vertices, caras):
    ruta = Path(ruta)
    with ruta.open('w', encoding='utf8') as f:
        f.write('# Escaneo3D: envolvente convexa experimental; escala no garantizada\n')
        for x, y, z in vertices:
            f.write(f'v {x:.12g} {y:.12g} {z:.12g}\n')
        for a, b, c in caras:
            f.write(f'f {a+1} {b+1} {c+1}\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('entrada', type=Path, help='JSON con clave puntos: [[x,y,z], ...]')
    ap.add_argument('--salida', required=True, type=Path, help='Archivo OBJ de salida')
    args = ap.parse_args()
    data = json.loads(args.entrada.read_text(encoding='utf8'))
    vertices, caras, volumen = generar_superficie(data['puntos'])
    guardar_obj(args.salida, vertices, caras)
    print(json.dumps({'vertices': len(vertices), 'caras': len(caras), 'volumen_unidades_cubicas': volumen,
                      'advertencia': 'Envolvente convexa: no conserva huecos ni concavidades; escala sin verificar.'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
