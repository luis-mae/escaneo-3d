"""Escalado métrico de una nube reconstruida con una distancia física conocida.

La calibración global NO corrige la deriva de escala entre pares de cámaras.
"""
import argparse
import json
from pathlib import Path
import numpy as np


def factor_escala(punto_a, punto_b, distancia_mm):
    a, b = np.asarray(punto_a, dtype=float), np.asarray(punto_b, dtype=float)
    d = float(distancia_mm)
    if a.shape != (3,) or b.shape != (3,) or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Referencias 3D inválidas')
    if not np.isfinite(d) or d <= 0:
        raise ValueError('Distancia física debe ser positiva y finita')
    baseline = float(np.linalg.norm(a - b))
    if baseline <= 1e-9:
        raise ValueError('Referencias coincidentes')
    return d / baseline


def escalar_nube(puntos, punto_a, punto_b, distancia_mm):
    pts = np.asarray(puntos, dtype=float)
    if pts.ndim != 2 or pts.shape[1] != 3 or not np.isfinite(pts).all():
        raise ValueError('Nube inválida')
    escala = factor_escala(punto_a, punto_b, distancia_mm)
    return pts * escala, {'factor': escala, 'unidad': 'mm', 'metodo': 'distancia_referencia',
                          'advertencia': 'Solo calibra escala global; no corrige deriva de cámaras ni certifica precisión.'}


def leer_ply_ascii(ruta):
    """Lee exclusivamente PLY ASCII con propiedades x,y,z como primeras columnas."""
    with Path(ruta).open(encoding='ascii') as f:
        if f.readline().strip() != 'ply' or f.readline().strip() != 'format ascii 1.0':
            raise ValueError('Solo se admite PLY ASCII 1.0')
        count = None
        props = []
        in_vertex = False
        for line in f:
            s = line.strip()
            if s.startswith('element '):
                parts = s.split()
                in_vertex = parts[1] == 'vertex'
                if in_vertex:
                    count = int(parts[2])
            elif s.startswith('property ') and in_vertex:
                props.append(s.split()[-1])
            elif s == 'end_header':
                break
        else:
            raise ValueError('Cabecera incompleta')
        if count is None or count < 0 or props[:3] != ['x', 'y', 'z']:
            raise ValueError('PLY sin coordenadas x,y,z válidas')
        points = []
        for _ in range(count):
            line = f.readline()
            if not line:
                raise ValueError('PLY truncado')
            fields = line.split()
            if len(fields) < 3:
                raise ValueError('Vértice inválido')
            points.append([float(x) for x in fields[:3]])
        return np.asarray(points, dtype=float).reshape((-1, 3))


def guardar_ply_ascii(ruta, puntos):
    pts = np.asarray(puntos, dtype=float)
    with Path(ruta).open('w', encoding='ascii') as f:
        f.write(f'ply\nformat ascii 1.0\nelement vertex {len(pts)}\nproperty float x\nproperty float y\nproperty float z\nend_header\n')
        for p in pts:
            f.write(' '.join(f'{x:.10g}' for x in p) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('nube', type=Path)
    parser.add_argument('--punto-a', nargs=3, type=float, required=True)
    parser.add_argument('--punto-b', nargs=3, type=float, required=True)
    parser.add_argument('--distancia-mm', type=float, required=True)
    parser.add_argument('--salida', type=Path, required=True)
    args = parser.parse_args()
    if args.nube.resolve() == args.salida.resolve():
        parser.error('La salida debe ser diferente del original')
    scaled, info = escalar_nube(leer_ply_ascii(args.nube), args.punto_a, args.punto_b, args.distancia_mm)
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    guardar_ply_ascii(args.salida, scaled)
    args.salida.with_suffix('.json').write_text(json.dumps(info, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(info, ensure_ascii=False))


if __name__ == '__main__':
    main()
