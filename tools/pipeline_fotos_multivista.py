"""Pipeline experimental fotos -> tracks -> poses encadenadas -> nube PLY.

ADVERTENCIA: las traslaciones entre pares tienen escala arbitraria e independiente.
No es reconstrucción métrica ni modelo imprimible. Requiere OpenCV y SciPy.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from tools.tracks_desde_fotos import extraer_tracks
from tools.poses_secuencia import estimar_secuencia
from tools.integrar_tracks_camaras import integrar_tracks
from tools.nube_dos_vistas import guardar_ply


def camaras_desde_poses(nombres, poses, focal_px, ancho, alto):
    if focal_px <= 0 or ancho <= 0 or alto <= 0 or len(nombres) != len(poses):
        raise ValueError('Calibración o cantidad de poses inválida')
    K = [[float(focal_px), 0., ancho / 2], [0., float(focal_px), alto / 2], [0., 0., 1.]]
    salida = {}
    for nombre, pose in zip(nombres, poses):
        R, t = np.asarray(pose['R'], float), np.asarray(pose['t'], float)
        if R.shape != (3, 3) or t.shape != (3,) or not np.isfinite(R).all() or not np.isfinite(t).all():
            raise ValueError('Pose inválida')
        salida[nombre] = {'K': K, 'R': R.tolist(), 't': t.tolist()}
    return salida


def procesar(fotos, focal_px, umbral_px=3.):
    import cv2
    fotos = [Path(p) for p in fotos]
    if len(fotos) < 3 or len({p.name for p in fotos}) != len(fotos):
        raise ValueError('Se requieren 3 o más fotos con nombres distintos')
    primera = cv2.imread(str(fotos[0]))
    if primera is None:
        raise ValueError('Primera foto ilegible')
    alto, ancho = primera.shape[:2]
    for foto in fotos[1:]:
        img = cv2.imread(str(foto))
        if img is None or img.shape[:2] != (alto, ancho):
            raise ValueError('Fotos ilegibles o de resoluciones diferentes')
    tracks = extraer_tracks(fotos)
    if any(par['estado'] != 'aceptado' for par in tracks['pares']):
        raise ValueError('Pares de fotografías sin suficientes correspondencias')
    poses = estimar_secuencia(fotos, focal_px)
    if poses['estado'] != 'experimental':
        raise ValueError('No se pudieron estimar todas las poses')
    camaras = camaras_desde_poses([p.name for p in fotos], poses['poses'], focal_px, ancho, alto)
    nube = integrar_tracks(camaras, tracks['puntos_por_imagen'], tracks['tracks'], umbral_px)
    if nube['aceptados'] < 3:
        raise ValueError('Nube insuficiente para una reconstrucción útil')
    return nube['puntos'], {
        'estado': 'experimental_no_metrico', 'fotografias': len(fotos),
        'tracks': tracks['total_tracks'], 'puntos_3d': nube['aceptados'],
        'tracks_rechazados': nube['rechazados'] + nube['tracks_descartados_entrada'],
        'pares': tracks['pares'],
        'advertencia': 'Poses encadenadas con baseline arbitrario por par: puede haber deformaciones. No usar para medidas, CAD o impresión 3D.'
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('fotos', nargs='+', type=Path)
    p.add_argument('--focal-px', type=float, required=True)
    p.add_argument('--salida', type=Path, required=True)
    args = p.parse_args()
    puntos, informe = procesar(args.fotos, args.focal_px)
    args.salida.mkdir(parents=True, exist_ok=True)
    guardar_ply(puntos, args.salida / 'nube_multivista.ply')
    (args.salida / 'informe.json').write_text(json.dumps(informe, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(informe, ensure_ascii=False))


if __name__ == '__main__':
    main()
