"""Estimación experimental de pose relativa entre dos fotografías calibradas.

Requiere opencv-python y numpy. La traslación tiene escala arbitraria:
NO permite obtener medidas métricas sin referencia externa.
"""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def estimar_pose(imagen_a, imagen_b, focal_px, centro=None, min_inliers=12):
    a = cv2.imread(str(imagen_a), cv2.IMREAD_GRAYSCALE)
    b = cv2.imread(str(imagen_b), cv2.IMREAD_GRAYSCALE)
    if a is None or b is None:
        raise ValueError('No se pudieron abrir ambas fotografías')
    if a.shape != b.shape:
        raise ValueError('Las fotografías deben tener la misma resolución')
    if focal_px <= 0:
        raise ValueError('La distancia focal en píxeles debe ser positiva')
    h, w = a.shape
    cx, cy = centro if centro is not None else (w / 2, h / 2)
    K = np.array([[focal_px, 0, cx], [0, focal_px, cy], [0, 0, 1.0]], dtype=np.float64)
    orb = cv2.ORB_create(nfeatures=3000)
    ka, da = orb.detectAndCompute(a, None)
    kb, db = orb.detectAndCompute(b, None)
    if da is None or db is None:
        return {'estado': 'insuficiente', 'motivo': 'Sin descriptores suficientes'}
    pairs = cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(da, db, k=2)
    good = [m for pair in pairs if len(pair) == 2 for m, n in [pair] if m.distance < 0.75 * n.distance]
    if len(good) < max(8, min_inliers):
        return {'estado': 'insuficiente', 'motivo': 'Pocas correspondencias', 'coincidencias': len(good)}
    pa = np.float64([ka[m.queryIdx].pt for m in good])
    pb = np.float64([kb[m.trainIdx].pt for m in good])
    E, mask = cv2.findEssentialMat(pa, pb, K, method=cv2.RANSAC, prob=0.999, threshold=1.5)
    if E is None:
        return {'estado': 'insuficiente', 'motivo': 'Geometría epipolar no estimable'}
    # OpenCV puede devolver varias matrices esenciales apiladas.
    if E.shape != (3, 3):
        E = E[:3, :]
    count, R, t, pose_mask = cv2.recoverPose(E, pa, pb, K, mask=mask)
    if count < min_inliers:
        return {'estado': 'insuficiente', 'motivo': 'Pocos puntos geométricamente consistentes', 'inliers': int(count)}
    return {
        'estado': 'experimental', 'coincidencias': len(good), 'inliers': int(count),
        'rotacion': R.tolist(), 'traslacion_direccion': t[:, 0].tolist(),
        'escala': 'desconocida',
        'advertencia': 'Pose relativa aproximada; no es una reconstrucción 3D ni una medición métrica.'
    }


def main():
    parser = argparse.ArgumentParser(description='Estimar pose relativa experimental entre dos fotos')
    parser.add_argument('foto1', type=Path)
    parser.add_argument('foto2', type=Path)
    parser.add_argument('--focal-px', type=float, required=True)
    parser.add_argument('--salida', type=Path)
    args = parser.parse_args()
    result = estimar_pose(args.foto1, args.foto2, args.focal_px)
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.salida:
        args.salida.write_text(output + '\n', encoding='utf-8')
    else:
        print(output)


if __name__ == '__main__':
    main()
