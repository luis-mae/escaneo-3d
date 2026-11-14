"""Integra tracks 2D con cámaras globales conocidas para triangular puntos 3D.

No estima cámaras ni garantiza precisión métrica sin referencia de escala.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from tools.nube_marco_comun import reconstruir_observaciones
from tools.nube_dos_vistas import guardar_ply


def integrar_tracks(camaras, puntos_por_imagen, tracks, umbral_px=2.0, min_vistas=2):
    """puntos_por_imagen: {id_imagen: [[x,y], ...]}; tracks: [{id_imagen: indice_punto}]."""
    if not isinstance(puntos_por_imagen, dict) or not isinstance(tracks, list):
        raise ValueError('Formato de entrada inválido')
    if not isinstance(camaras, dict) or len(camaras) < 2:
        raise ValueError('Se requieren al menos dos cámaras identificadas')
    nombres = sorted(camaras, key=str)
    indices = {nombre: i for i, nombre in enumerate(nombres)}
    pistas, descartadas = [], 0
    for n, track in enumerate(tracks):
        if not isinstance(track, dict) or len(track) < min_vistas:
            descartadas += 1
            continue
        obs = []
        for nombre, idx in track.items():
            if nombre not in indices or nombre not in puntos_por_imagen or not isinstance(idx, int) or isinstance(idx, bool):
                break
            puntos = puntos_por_imagen[nombre]
            if idx < 0 or idx >= len(puntos):
                break
            xy = np.asarray(puntos[idx], dtype=float)
            if xy.shape != (2,) or not np.isfinite(xy).all():
                break
            obs.append({'camara': indices[nombre], 'xy': xy.tolist()})
        else:
            pistas.append({'id': n, 'observaciones': obs})
            continue
        descartadas += 1
    resultado = reconstruir_observaciones([camaras[n] for n in nombres], pistas, umbral_px, min_vistas)
    resultado['tracks_descartados_entrada'] = descartadas
    resultado['camaras_ordenadas'] = nombres
    return resultado


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('entrada', type=Path)
    parser.add_argument('--salida', type=Path, required=True)
    parser.add_argument('--umbral-px', type=float, default=2.0)
    args = parser.parse_args()
    datos = json.loads(args.entrada.read_text(encoding='utf-8'))
    resultado = integrar_tracks(datos['camaras'], datos['puntos_por_imagen'], datos['tracks'], args.umbral_px)
    args.salida.mkdir(parents=True, exist_ok=True)
    guardar_ply(resultado['puntos'], args.salida / 'nube_tracks.ply')
    (args.salida / 'informe.json').write_text(json.dumps({k: v for k, v in resultado.items() if k != 'puntos'}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"Puntos 3D: {resultado['aceptados']}; descartados: {resultado['rechazados'] + resultado['tracks_descartados_entrada']}")


if __name__ == '__main__':
    main()
