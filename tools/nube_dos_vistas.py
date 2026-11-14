"""Nube dispersa experimental desde dos fotos. Escala arbitraria, no apta para imprimir."""
import argparse
import json
from pathlib import Path
import cv2
import numpy as np
from tools.triangular_puntos import triangular_puntos


def reconstruir_par(foto_a, foto_b, focal_px, min_puntos=12):
    a = cv2.imread(str(foto_a), cv2.IMREAD_GRAYSCALE)
    b = cv2.imread(str(foto_b), cv2.IMREAD_GRAYSCALE)
    if a is None or b is None or a.shape != b.shape:
        raise ValueError('Se requieren dos fotos legibles de igual resolución')
    if not np.isfinite(focal_px) or focal_px <= 0:
        raise ValueError('Focal en píxeles inválida')
    h, w = a.shape
    K = np.array([[focal_px, 0, w/2], [0, focal_px, h/2], [0, 0, 1.]], dtype=float)
    orb = cv2.ORB_create(nfeatures=4000)
    ka, da = orb.detectAndCompute(a, None)
    kb, db = orb.detectAndCompute(b, None)
    if da is None or db is None:
        return {'estado': 'insuficiente', 'motivo': 'Sin puntos de interés'}
    matches = cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(da, db, k=2)
    good = [m for pair in matches if len(pair) == 2 for m, n in [pair] if m.distance < .75*n.distance]
    if len(good) < max(min_puntos, 8):
        return {'estado': 'insuficiente', 'motivo': 'Pocas correspondencias', 'coincidencias': len(good)}
    pa = np.float64([ka[m.queryIdx].pt for m in good]); pb = np.float64([kb[m.trainIdx].pt for m in good])
    E, mask = cv2.findEssentialMat(pa, pb, K, method=cv2.RANSAC, prob=.999, threshold=1.5)
    if E is None:
        return {'estado': 'insuficiente', 'motivo': 'No se estimó geometría epipolar'}
    if E.shape != (3, 3): E = E[:3, :]
    count, R, t, pose_mask = cv2.recoverPose(E, pa, pb, K, mask=mask)
    selected = pose_mask.ravel() != 0
    if count < min_puntos:
        return {'estado': 'insuficiente', 'motivo': 'Pocos puntos consistentes', 'inliers': int(count)}
    result = triangular_puntos(pa[selected], pb[selected], K, R, t)
    return {'estado': 'experimental', 'coincidencias': len(good), 'inliers': int(count),
            'puntos': result['puntos'], 'aceptados': result['aceptados'],
            'rechazados': result['rechazados'], 'escala': 'arbitraria',
            'advertencia': 'Nube dispersa sin escala métrica; no es malla ni modelo imprimible.'}


def guardar_ply(puntos, destino):
    coords = np.asarray(puntos, dtype=float)
    if coords.ndim != 2 or coords.shape[1] != 3 or not np.isfinite(coords).all():
        raise ValueError('La nube debe contener puntos Nx3 finitos')
    with open(destino, 'w', encoding='ascii') as f:
        f.write('ply\nformat ascii 1.0\n')
        f.write(f'element vertex {len(coords)}\nproperty float x\nproperty float y\nproperty float z\nend_header\n')
        for x, y, z in coords: f.write(f'{x:.9g} {y:.9g} {z:.9g}\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('foto1', type=Path); p.add_argument('foto2', type=Path)
    p.add_argument('--focal-px', type=float, required=True)
    p.add_argument('--ply', type=Path, required=True)
    p.add_argument('--informe', type=Path)
    args = p.parse_args()
    result = reconstruir_par(args.foto1, args.foto2, args.focal_px)
    if result['estado'] == 'experimental' and result['aceptados']:
        guardar_ply(result['puntos'], args.ply)
    if args.informe:
        args.informe.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    else:
        print(json.dumps({k: v for k, v in result.items() if k != 'puntos'}, ensure_ascii=False, indent=2))

if __name__ == '__main__': main()
