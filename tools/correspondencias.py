"""Detecta correspondencias entre dos fotografías usando ORB y RANSAC.

Diagnóstico de solapamiento; NO reconstruye una malla ni estima escala métrica.
Requiere opencv-python y numpy opcionales.
"""
import argparse
import json
from pathlib import Path


def comparar(imagen_a: Path, imagen_b: Path, minimo: int = 12) -> dict:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError('Instalá opencv-python para analizar correspondencias') from exc
    if minimo < 4:
        raise ValueError('El mínimo debe ser al menos 4')
    a = cv2.imread(str(imagen_a), cv2.IMREAD_GRAYSCALE)
    b = cv2.imread(str(imagen_b), cv2.IMREAD_GRAYSCALE)
    if a is None or b is None:
        raise ValueError('No se pudieron abrir ambas fotografías')
    orb = cv2.ORB_create(nfeatures=2000)
    ka, da = orb.detectAndCompute(a, None)
    kb, db = orb.detectAndCompute(b, None)
    if da is None or db is None or len(ka) < 4 or len(kb) < 4:
        return {'puntos_a': len(ka), 'puntos_b': len(kb), 'coincidencias': 0, 'inliers': 0, 'apta': False}
    pares = cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(da, db, k=2)
    buenas = [m for par in pares if len(par) == 2 for m, n in [par] if m.distance < 0.75 * n.distance]
    inliers = 0
    if len(buenas) >= 8:
        import numpy as np
        pa = np.float32([ka[m.queryIdx].pt for m in buenas])
        pb = np.float32([kb[m.trainIdx].pt for m in buenas])
        _, mascara = cv2.findFundamentalMat(pa, pb, cv2.FM_RANSAC, 2.0, 0.99)
        if mascara is not None:
            inliers = int(mascara.ravel().sum())
    return {'puntos_a': len(ka), 'puntos_b': len(kb), 'coincidencias': len(buenas),
            'inliers': inliers, 'apta': inliers >= minimo,
            'advertencia': 'Coincidencias visuales no garantizan reconstrucción 3D.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('imagen_a', type=Path)
    p.add_argument('imagen_b', type=Path)
    p.add_argument('--minimo', type=int, default=12)
    a = p.parse_args()
    print(json.dumps(comparar(a.imagen_a, a.imagen_b, a.minimo), ensure_ascii=False, indent=2))
