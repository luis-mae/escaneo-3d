"""Registro ICP experimental y fusión de nubes 3D (sin escala métrica garantizada).

Las nubes deben estar aproximadamente alineadas: ICP puede converger a mínimos locales.
"""
import argparse
import json
from pathlib import Path
import numpy as np

try:
    from tools.alinear_nubes import estimar_similitud, transformar
except ModuleNotFoundError:
    from alinear_nubes import estimar_similitud, transformar


def validar(p):
    p = np.asarray(p, dtype=float)
    if p.ndim != 2 or p.shape[1] != 3 or len(p) < 3 or not np.isfinite(p).all():
        raise ValueError('Nube inválida: se requieren al menos tres puntos 3D finitos')
    return p


def vecinos(p, q, bloque=512):
    indices, distancias = [], []
    for inicio in range(0, len(p), bloque):
        dist2 = np.sum((p[inicio:inicio+bloque, None] - q[None, :])**2, axis=2)
        idx = np.argmin(dist2, axis=1)
        indices.extend(idx.tolist())
        distancias.extend(np.sqrt(dist2[np.arange(len(idx)), idx]).tolist())
    return np.asarray(indices), np.asarray(distancias)


def icp(origen, destino, iteraciones=35, fraccion=0.85, tolerancia=1e-7):
    a, b = validar(origen), validar(destino)
    if not (0.5 <= fraccion <= 1.0):
        raise ValueError('fraccion debe estar entre 0.5 y 1')
    actual = a.copy()
    previo = float('inf')
    ajustes = []
    for _ in range(iteraciones):
        idx, dist = vecinos(actual, b)
        n = max(3, int(np.ceil(len(actual) * fraccion)))
        seleccion = np.argsort(dist)[:n]
        ajuste = estimar_similitud(actual[seleccion], b[idx[seleccion]])
        # ICP rígido: evita alterar arbitrariamente las dimensiones entre iteraciones.
        ajuste['escala'] = 1.0
        # Recalcular traslación para la rotación rígida elegida.
        rot = np.asarray(ajuste['rotacion'])
        ajuste['traslacion'] = (b[idx[seleccion]].mean(axis=0) - actual[seleccion].mean(axis=0) @ rot).tolist()
        actual = transformar(actual, ajuste)
        ajustes.append(ajuste)
        _, nuevos = vecinos(actual, b)
        error = float(np.sqrt(np.mean(np.sort(nuevos)[:n]**2)))
        if abs(previo - error) < tolerancia:
            break
        previo = error
    return actual, {'iteraciones': len(ajustes), 'error_rms': error,
                    'advertencia': 'ICP experimental: requiere solapamiento y alineación inicial; no garantiza exactitud métrica.'}


def fusionar(nubes, voxel=0.001):
    if voxel <= 0 or not np.isfinite(voxel):
        raise ValueError('voxel debe ser positivo y finito')
    puntos = np.concatenate([validar(n) for n in nubes], axis=0)
    celdas = np.floor(puntos / voxel).astype(np.int64)
    _, inv = np.unique(celdas, axis=0, return_inverse=True)
    conteo = np.bincount(inv)
    return np.column_stack([np.bincount(inv, weights=puntos[:, j]) / conteo for j in range(3)])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('entrada', type=Path, help='JSON: {"nubes": [[[x,y,z], ...], ...]}')
    ap.add_argument('--salida', required=True, type=Path)
    ap.add_argument('--voxel', type=float, default=0.001)
    args = ap.parse_args()
    nubes = json.loads(args.entrada.read_text(encoding='utf8'))['nubes']
    if len(nubes) < 2:
        raise ValueError('Se necesitan al menos dos nubes')
    referencia = validar(nubes[0]); alineadas = [referencia]; informes = []
    for nube in nubes[1:]:
        ajustada, info = icp(nube, referencia)
        alineadas.append(ajustada); informes.append(info)
    resultado = {'puntos': fusionar(alineadas, args.voxel).tolist(), 'registros': informes,
                 'unidad': 'desconocida; depende de la calibración de entrada'}
    args.salida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(f"Nube unificada: {len(resultado['puntos'])} puntos")


if __name__ == '__main__':
    main()
