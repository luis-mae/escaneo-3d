"""Ajuste multivista experimental de puntos y cámaras (bundle adjustment).

Requiere calibración K y poses iniciales razonables. Fija las dos primeras
cámaras para eliminar ambigüedad de escala/origen; NO recupera escala métrica.
"""
import numpy as np
import cv2
from scipy.optimize import least_squares


def ajustar(camaras, observaciones, puntos, max_nfev=120, umbral_px=5.0):
    """Cámaras: lista de dicts K,R,t; observaciones: (cam, punto, u, v).

    Devuelve copias de cámaras/puntos ajustados, error RMS y estado. Las cámaras
    0 y 1 se mantienen fijas para anclar el sistema de coordenadas y escala.
    """
    if len(camaras) < 2:
        raise ValueError('Se requieren dos cámaras para fijar la escala')
    X = np.asarray(puntos, dtype=float)
    obs = np.asarray(observaciones, dtype=float)
    if X.ndim != 2 or X.shape[1] != 3 or not len(X) or not np.isfinite(X).all():
        raise ValueError('Puntos 3D inválidos')
    if obs.ndim != 2 or obs.shape[1] != 4 or len(obs) < 4 or not np.isfinite(obs).all():
        raise ValueError('Observaciones inválidas')
    ci, pi = obs[:, 0].astype(int), obs[:, 1].astype(int)
    if np.any(ci != obs[:, 0]) or np.any(pi != obs[:, 1]) or np.any(ci < 0) or np.any(ci >= len(camaras)) or np.any(pi < 0) or np.any(pi >= len(X)):
        raise ValueError('Índices de observaciones inválidos')
    Ks, Rs, ts = [], [], []
    for c in camaras:
        K, R, t = (np.asarray(c[k], dtype=float) for k in ('K', 'R', 't'))
        if K.shape != (3, 3) or R.shape != (3, 3) or t.shape != (3,) or not np.isfinite(K).all() or not np.isfinite(R).all() or not np.isfinite(t).all():
            raise ValueError('Cámara inválida')
        Ks.append(K); Rs.append(R); ts.append(t)
    # Sólo optimizar cámaras posteriores a la segunda; primeras dos fijas.
    extra = []
    for R, t in zip(Rs[2:], ts[2:]):
        rv, _ = cv2.Rodrigues(R)
        extra.extend(rv.ravel()); extra.extend(t)
    x0 = np.r_[X.ravel(), extra]
    n = len(X)

    def unpack(z):
        pts = z[:3*n].reshape(n, 3)
        rot, trans = list(Rs[:2]), list(ts[:2])
        for j in range(2, len(camaras)):
            off = 3*n + 6*(j-2)
            r, _ = cv2.Rodrigues(z[off:off+3])
            rot.append(r); trans.append(z[off+3:off+6])
        return pts, rot, trans

    def residual(z):
        pts, rot, trans = unpack(z)
        errors = []
        for k, idx in enumerate(ci):
            p = rot[idx] @ pts[pi[k]] + trans[idx]
            if p[2] <= 1e-8:
                errors.extend([1e3, 1e3])
            else:
                q = Ks[idx] @ p
                errors.extend(q[:2]/q[2] - obs[k, 2:4])
        return np.asarray(errors)

    initial = residual(x0)
    fit = least_squares(residual, x0, loss='soft_l1', f_scale=umbral_px, max_nfev=max_nfev)
    pts, rot, trans = unpack(fit.x)
    final = residual(fit.x)
    return {
        'estado': 'experimental' if fit.success else 'no_convergente',
        'puntos': pts.tolist(),
        'camaras': [{'K': Ks[j].tolist(), 'R': rot[j].tolist(), 't': trans[j].tolist()} for j in range(len(camaras))],
        'rms_inicial_px': float(np.sqrt(np.mean(initial**2))),
        'rms_final_px': float(np.sqrt(np.mean(final**2))),
        'observaciones': len(obs),
        'advertencia': 'Requiere cámaras calibradas y puntos iniciales. Escala arbitraria; no validado con imágenes reales.'
    }
