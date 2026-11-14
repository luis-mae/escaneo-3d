"""Estimación experimental de poses de una secuencia de fotos.

Encadena poses relativas adyacentes. Cada baseline se fija arbitrariamente en
una unidad: NO resuelve escala relativa, cierre de bucle ni bundle adjustment.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from tools.estimar_camaras import estimar_pose


def encadenar_poses(relativas):
    """Devuelve extrínsecas world->camera para una cadena de poses relativas."""
    R = np.eye(3)
    t = np.zeros(3)
    salida = [{'R': R.tolist(), 't': t.tolist()}]
    for paso in relativas:
        if paso.get('estado') != 'experimental':
            raise ValueError('Par sin pose relativa válida')
        r = np.asarray(paso['rotacion'], dtype=float)
        d = np.asarray(paso['traslacion_direccion'], dtype=float).reshape(-1)
        if (r.shape != (3, 3) or d.shape != (3,) or
            not np.isfinite(r).all() or not np.isfinite(d).all() or
            not np.allclose(r @ r.T, np.eye(3), atol=1e-3) or
            not np.isclose(np.linalg.det(r), 1.0, atol=1e-3) or
            not np.isclose(np.linalg.norm(d), 1.0, atol=1e-2)):
            raise ValueError('Pose relativa inválida')
        R, t = r @ R, r @ t + d
        salida.append({'R': R.tolist(), 't': t.tolist()})
    return salida


def estimar_secuencia(fotos, focal_px, min_inliers=12):
    if len(fotos) < 2:
        raise ValueError('Se requieren al menos dos fotografías')
    pares = []
    for a, b in zip(fotos, fotos[1:]):
        resultado = estimar_pose(a, b, focal_px, min_inliers=min_inliers)
        pares.append({'foto_a': str(a), 'foto_b': str(b), **resultado})
        if resultado.get('estado') != 'experimental':
            return {'estado': 'insuficiente', 'pares': pares, 'motivo': 'Falla de estimación en un par; secuencia interrumpida'}
    return {'estado': 'experimental', 'pares': pares,
            'poses': encadenar_poses(pares),
            'escala': 'arbitraria_por_par',
            'advertencia': 'Las traslaciones por par tienen escala independiente. Las poses NO son una calibración global métrica; requieren ajuste multivista.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('fotos', nargs='+', type=Path)
    p.add_argument('--focal-px', type=float, required=True)
    p.add_argument('--salida', type=Path, required=True)
    args = p.parse_args()
    resultado = estimar_secuencia(args.fotos, args.focal_px)
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(resultado, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(resultado['estado'])


if __name__ == '__main__':
    main()
