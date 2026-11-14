"""Reconstrucción dispersa experimental desde dos fotos, sin escala métrica.

No produce una superficie ni sustituye SfM multivista con ajuste global.
"""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def triangular_filtrado(pa, pb, K, R, t, max_error_px=3.0, min_paralaje_grados=0.5):
    """Triangula puntos correspondientes y descarta profundidad/reproyección/paralaje malos."""
    pa, pb = np.asarray(pa, dtype=np.float64), np.asarray(pb, dtype=np.float64)
    K, R = np.asarray(K, dtype=np.float64), np.asarray(R, dtype=np.float64)
    t = np.asarray(t, dtype=np.float64).reshape(3, 1)
    if pa.ndim != 2 or pa.shape[1] != 2 or pb.shape != pa.shape:
        raise ValueError('Correspondencias Nx2 incompatibles')
    if not len(pa):
        return np.empty((0, 3)), np.zeros(0, dtype=bool)
    P1 = K @ np.hstack([np.eye(3), np.zeros((3, 1))])
    P2 = K @ np.hstack([R, t])
    homog = cv2.triangulatePoints(P1, P2, pa.T, pb.T)
    valid_w = np.abs(homog[3]) > 1e-10
    xyz = np.full((len(pa), 3), np.nan)
    xyz[valid_w] = (homog[:3, valid_w] / homog[3, valid_w]).T
    cam2 = (R @ xyz.T + t).T
    good = valid_w & np.isfinite(xyz).all(axis=1) & (xyz[:, 2] > 0) & (cam2[:, 2] > 0)
    with np.errstate(invalid='ignore', divide='ignore'):
        proj1 = (P1 @ np.c_[xyz, np.ones(len(xyz))].T).T
        proj2 = (P2 @ np.c_[xyz, np.ones(len(xyz))].T).T
        uv1, uv2 = proj1[:, :2] / proj1[:, 2:3], proj2[:, :2] / proj2[:, 2:3]
        err = np.maximum(np.linalg.norm(uv1 - pa, axis=1), np.linalg.norm(uv2 - pb, axis=1))
        c2 = -(R.T @ t).ravel()
        v1, v2 = xyz, xyz - c2
        cosine = np.sum(v1 * v2, axis=1) / (np.linalg.norm(v1, axis=1) * np.linalg.norm(v2, axis=1))
        angle = np.degrees(np.arccos(np.clip(cosine, -1, 1)))
    good &= (err <= max_error_px) & (angle >= min_paralaje_grados)
    return xyz[good], good


def reconstruir(foto_a, foto_b, focal_px, max_error_px=3.0):
    a, b = cv2.imread(str(foto_a)), cv2.imread(str(foto_b))
    if a is None or b is None or a.shape[:2] != b.shape[:2]:
        raise ValueError('Fotografías ilegibles o de diferente resolución')
    if focal_px <= 0:
        raise ValueError('focal_px debe ser positivo')
    h, w = a.shape[:2]
    K = np.array([[focal_px, 0, w / 2], [0, focal_px, h / 2], [0, 0, 1.]], dtype=float)
    orb = cv2.ORB_create(nfeatures=4000)
    k1, d1 = orb.detectAndCompute(cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), None)
    k2, d2 = orb.detectAndCompute(cv2.cvtColor(b, cv2.COLOR_BGR2GRAY), None)
    if d1 is None or d2 is None or len(d1) < 12 or len(d2) < 12:
        raise ValueError('No hay suficientes características en las fotografías')
    pairs = cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(d1, d2, k=2)
    matches = [m for pair in pairs if len(pair) == 2 for m, n in [pair] if m.distance < .75 * n.distance]
    if len(matches) < 12:
        raise ValueError('Menos de 12 correspondencias fiables')
    pa = np.array([k1[m.queryIdx].pt for m in matches], dtype=np.float64)
    pb = np.array([k2[m.trainIdx].pt for m in matches], dtype=np.float64)
    E, mask = cv2.findEssentialMat(pa, pb, K, cv2.RANSAC, .999, 1.5)
    if E is None:
        raise ValueError('No se pudo estimar la geometría esencial')
    n, R, t, inlier_mask = cv2.recoverPose(E[:3, :], pa, pb, K, mask=mask)
    keep = inlier_mask.ravel() != 0
    if n < 12:
        raise ValueError('Muy pocos puntos consistentes con la pose')
    xyz, accepted = triangular_filtrado(pa[keep], pb[keep], K, R, t, max_error_px)
    if len(xyz) < 8:
        raise ValueError('Triangulación insuficiente tras filtrar puntos')
    return xyz, {'estado': 'experimental', 'coincidencias': len(matches), 'inliers_pose': int(n),
                 'puntos_3d': len(xyz), 'rechazados_triangulacion': int(len(accepted) - accepted.sum()),
                 'escala': 'arbitraria', 'nota': 'No apto para medidas ni impresión sin validación y escala externa.'}


def guardar_ply(ruta, xyz):
    xyz = np.asarray(xyz, dtype=float)
    with Path(ruta).open('w', encoding='ascii') as f:
        f.write('ply\nformat ascii 1.0\n')
        f.write(f'element vertex {len(xyz)}\nproperty float x\nproperty float y\nproperty float z\nend_header\n')
        for x, y, z in xyz:
            f.write(f'{x:.9g} {y:.9g} {z:.9g}\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('foto_a', type=Path)
    p.add_argument('foto_b', type=Path)
    p.add_argument('--focal-px', type=float, required=True)
    p.add_argument('--salida', type=Path, required=True)
    args = p.parse_args()
    xyz, report = reconstruir(args.foto_a, args.foto_b, args.focal_px)
    guardar_ply(args.salida, xyz)
    args.salida.with_suffix('.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
