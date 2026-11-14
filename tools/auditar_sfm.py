"""Auditoría geométrica de SfM disperso por reproyección y profundidad.

No mide exactitud física ni certifica una reconstrucción.
"""
import numpy as np


def auditar_sfm(puntos, indices_tracks, observaciones, camaras, K, umbral_px=3.0):
    xyz = np.asarray(puntos, dtype=float)
    matriz = np.asarray(K, dtype=float)
    if xyz.ndim != 2 or xyz.shape[1] != 3 or not np.isfinite(xyz).all():
        raise ValueError("Puntos 3D inválidos")
    if matriz.shape != (3, 3) or not np.isfinite(matriz).all():
        raise ValueError("Matriz intrínseca inválida")
    if not np.isfinite(umbral_px) or umbral_px <= 0:
        raise ValueError("Umbral inválido")
    if len(indices_tracks) != len(xyz):
        raise ValueError("Índices de tracks inconsistentes")
    errores = []
    positivas = 0
    total = 0
    por_camara = {}
    for X, indice in zip(xyz, indices_tracks):
        obs = observaciones[indice]
        for nombre, uv in obs.items():
            if nombre not in camaras:
                continue
            R, t = camaras[nombre]
            local = np.asarray(R) @ X + np.asarray(t)
            total += 1
            if local[2] <= 1e-8 or not np.isfinite(local).all():
                continue
            positivas += 1
            proyectado = matriz @ local
            err = float(np.linalg.norm(proyectado[:2] / proyectado[2] - uv))
            if not np.isfinite(err):
                continue
            errores.append(err)
            por_camara.setdefault(nombre, []).append(err)
    rms = float(np.sqrt(np.mean(np.square(errores)))) if errores else None
    p95 = float(np.percentile(errores, 95)) if errores else None
    return {"observaciones_totales": total, "profundidad_positiva": positivas,
            "observaciones_evaluadas": len(errores),
            "cobertura_profundidad": float(positivas / total) if total else 0.0,
            "rms_reproyeccion_px": rms, "p95_reproyeccion_px": p95,
            "fraccion_bajo_umbral": float(np.mean(np.asarray(errores) <= umbral_px)) if errores else 0.0,
            "por_camara": {k: {"observaciones": len(v),
                                "rms_px": float(np.sqrt(np.mean(np.square(v))))}
                           for k, v in por_camara.items()},
            "advertencia": "Auditoría interna de reproyección, no verifica dimensiones reales."}
