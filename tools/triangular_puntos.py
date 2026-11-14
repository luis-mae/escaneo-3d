"""Triangulación dispersa entre dos vistas calibradas (escala arbitraria).

No produce una malla cerrada ni medidas físicas sin calibración externa.
"""
import numpy as np
import cv2


def triangular_puntos(puntos_a, puntos_b, intrinseca, rotacion, traslacion,
                      error_max_px=3.0, profundidad_min=1e-6):
    a = np.asarray(puntos_a, dtype=np.float64)
    b = np.asarray(puntos_b, dtype=np.float64)
    K = np.asarray(intrinseca, dtype=np.float64)
    R = np.asarray(rotacion, dtype=np.float64)
    t = np.asarray(traslacion, dtype=np.float64).reshape(3, 1)
    if a.ndim != 2 or a.shape[1] != 2 or b.shape != a.shape:
        raise ValueError('Se requieren pares de puntos Nx2')
    if K.shape != (3, 3) or R.shape != (3, 3) or len(a) < 2:
        raise ValueError('Calibración inválida o correspondencias insuficientes')
    if not all(np.isfinite(x).all() for x in (a, b, K, R, t)):
        raise ValueError('Datos no finitos')
    if error_max_px <= 0 or np.linalg.norm(t) < 1e-9:
        raise ValueError('Umbral o línea base inválidos')
    P1 = K @ np.column_stack((np.eye(3), np.zeros(3)))
    P2 = K @ np.column_stack((R, t))
    homogeneous = cv2.triangulatePoints(P1, P2, a.T, b.T)
    w = homogeneous[3]
    valid_w = np.abs(w) > 1e-10
    xyz = np.full((len(a), 3), np.nan)
    xyz[valid_w] = (homogeneous[:3, valid_w] / w[valid_w]).T
    z1 = xyz[:, 2]
    z2 = (R @ xyz.T + t)[2]
    with np.errstate(divide='ignore', invalid='ignore'):
        q1 = (P1 @ np.column_stack((xyz, np.ones(len(xyz)))).T).T
        q2 = (P2 @ np.column_stack((xyz, np.ones(len(xyz)))).T).T
        reproj1 = q1[:, :2] / q1[:, 2:3]
        reproj2 = q2[:, :2] / q2[:, 2:3]
        error = np.maximum(np.linalg.norm(reproj1 - a, axis=1), np.linalg.norm(reproj2 - b, axis=1))
    valid = valid_w & (z1 > profundidad_min) & (z2 > profundidad_min) & (error <= error_max_px) & np.isfinite(error)
    return {'puntos': xyz[valid].tolist(), 'aceptados': int(valid.sum()),
            'rechazados': int((~valid).sum()), 'indices_aceptados': np.flatnonzero(valid).tolist(),
            'escala': 'arbitraria', 'tipo': 'nube_de_puntos_dispersos'}
