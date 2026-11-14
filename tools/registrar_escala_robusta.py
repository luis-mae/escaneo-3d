"""Registro robusto Sim(3) con RANSAC para correspondencias 3D conocidas.

No encuentra correspondencias automáticamente ni sustituye ajuste multivista.
"""
import argparse
import json
from pathlib import Path
import numpy as np

try:
    from .registrar_escala import estimar_similitud, transformar_puntos
except ImportError:
    from registrar_escala import estimar_similitud, transformar_puntos


def estimar_similitud_robusta(origen, destino, umbral, iteraciones=500, semilla=0, minimo_inliers=3):
    a, b = np.asarray(origen, dtype=float), np.asarray(destino, dtype=float)
    if a.ndim != 2 or a.shape[1:] != (3,) or a.shape != b.shape or len(a) < 3:
        raise ValueError('Se requieren al menos tres pares 3D')
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Coordenadas no finitas')
    if not np.isfinite(umbral) or umbral <= 0 or iteraciones < 1 or minimo_inliers < 3:
        raise ValueError('Parámetros RANSAC inválidos')
    rng = np.random.default_rng(semilla)
    mejor = None
    for _ in range(iteraciones):
        idx = rng.choice(len(a), 3, replace=False)
        try:
            candidato = estimar_similitud(a[idx], b[idx])
        except ValueError:
            continue
        residuos = np.linalg.norm(transformar_puntos(a, candidato) - b, axis=1)
        mascara = residuos <= umbral
        cantidad = int(mascara.sum())
        puntuacion = (cantidad, -float(np.median(residuos[mascara])) if cantidad else -np.inf)
        if mejor is None or puntuacion > mejor[0]:
            mejor = (puntuacion, mascara)
    if mejor is None or mejor[0][0] < minimo_inliers:
        raise ValueError('No se encontró consenso geométrico suficiente')
    mascara = mejor[1]
    for _ in range(5):
        ajuste = estimar_similitud(a[mascara], b[mascara])
        residuos = np.linalg.norm(transformar_puntos(a, ajuste) - b, axis=1)
        nueva = residuos <= umbral
        if nueva.sum() < minimo_inliers:
            break
        if np.array_equal(nueva, mascara):
            break
        mascara = nueva
    ajuste = estimar_similitud(a[mascara], b[mascara])
    residuos = np.linalg.norm(transformar_puntos(a, ajuste) - b, axis=1)
    ajuste.update({'inliers': np.flatnonzero(mascara).tolist(),
                   'outliers': np.flatnonzero(~mascara).tolist(),
                   'total_correspondencias': len(a), 'umbral': float(umbral),
                   'rmse_inliers': float(np.sqrt(np.mean(residuos[mascara]**2))),
                   'estado': 'registro_robusto_por_referencias'})
    return ajuste


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('correspondencias', type=Path)
    p.add_argument('--salida', type=Path, required=True)
    p.add_argument('--umbral', type=float, required=True, help='Umbral en unidades de destino')
    p.add_argument('--iteraciones', type=int, default=500)
    args = p.parse_args()
    data = json.loads(args.correspondencias.read_text(encoding='utf-8'))
    resultado = estimar_similitud_robusta(data['origen'], data['destino'], args.umbral, args.iteraciones)
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(resultado, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')

if __name__ == '__main__':
    main()
