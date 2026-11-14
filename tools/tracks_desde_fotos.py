"""Extrae puntos ORB y tracks multivista de fotografías reales.

No estima poses, escala ni geometría 3D. Requiere OpenCV.
"""
import argparse
import json
from pathlib import Path
import cv2
import numpy as np
from tools.tracks_multivista import construir_tracks


def emparejar_descriptores(desc_a, desc_b, ratio=0.75):
    """Correspondencias recíprocas filtradas por razón de Lowe."""
    if not 0 < ratio < 1:
        raise ValueError('ratio debe estar entre 0 y 1')
    if desc_a is None or desc_b is None or len(desc_a) < 2 or len(desc_b) < 2:
        return []
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    def candidatos(a, b):
        return {m.queryIdx: m.trainIdx for par in matcher.knnMatch(a, b, k=2)
                if len(par) == 2 for m, n in [par] if m.distance < ratio*n.distance}
    ab, ba = candidatos(desc_a, desc_b), candidatos(desc_b, desc_a)
    return sorted((i, j) for i, j in ab.items() if ba.get(j) == i)


def extraer_tracks(rutas, max_features=3000, min_inliers=12, ratio=0.75):
    if len(rutas) < 2:
        raise ValueError('Se necesitan al menos dos fotografías')
    if max_features < 50 or min_inliers < 8:
        raise ValueError('Parámetros fuera de rango')
    nombres = [Path(p).name for p in rutas]
    if len(set(nombres)) != len(nombres):
        raise ValueError('Los nombres de las fotografías deben ser únicos')
    orb = cv2.ORB_create(nfeatures=max_features)
    puntos, descriptores = {}, {}
    for ruta, nombre in zip(rutas, nombres):
        img = cv2.imread(str(ruta), cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f'No se puede leer: {ruta}')
        kp, desc = orb.detectAndCompute(img, None)
        puntos[nombre] = [[float(x), float(y)] for x, y in (k.pt for k in kp)]
        descriptores[nombre] = desc
    edges, pares = [], []
    for a, b in zip(nombres[:-1], nombres[1:]):
        matches = emparejar_descriptores(descriptores[a], descriptores[b], ratio)
        inliers = []
        if len(matches) >= 8:
            pa = np.float32([puntos[a][i] for i, _ in matches])
            pb = np.float32([puntos[b][j] for _, j in matches])
            _, mask = cv2.findFundamentalMat(pa, pb, cv2.FM_RANSAC, 1.5, 0.99)
            if mask is not None and len(mask) == len(matches):
                inliers = [m for m, valid in zip(matches, mask.ravel()) if valid]
        if len(inliers) >= min_inliers:
            edges.extend((a, i, b, j) for i, j in inliers)
            estado = 'aceptado'
        else:
            estado = 'insuficiente'
        pares.append({'a': a, 'b': b, 'matches': len(matches), 'inliers': len(inliers), 'estado': estado})
    tracks = construir_tracks(edges)
    return {'puntos_por_imagen': puntos, 'tracks': tracks['tracks'], 'pares': pares,
            'total_tracks': tracks['total_tracks'], 'correspondencias_rechazadas': tracks['correspondencias_rechazadas'],
            'advertencia': 'Solo correspondencias 2D; faltan poses globales, escala y validación con imágenes reales.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fotos', nargs='+', type=Path)
    parser.add_argument('--salida', required=True, type=Path)
    parser.add_argument('--min-inliers', type=int, default=12)
    args = parser.parse_args()
    resultado = extraer_tracks(args.fotos, min_inliers=args.min_inliers)
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"Tracks: {resultado['total_tracks']}; pares aceptados: {sum(p['estado']=='aceptado' for p in resultado['pares'])}")

if __name__ == '__main__':
    main()
