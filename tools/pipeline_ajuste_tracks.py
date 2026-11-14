"""Conecta tracks multivista triangulados con bundle adjustment.

Requiere poses y calibraciones iniciales globales; no las infiere de fotos.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from tools.integrar_tracks_camaras import integrar_tracks
from tools.ajuste_multivista import ajustar
from tools.nube_dos_vistas import guardar_ply


def reconstruir_y_ajustar(camaras, puntos_por_imagen, tracks, umbral_px=3.0, max_nfev=120):
    base = integrar_tracks(camaras, puntos_por_imagen, tracks, umbral_px=umbral_px)
    nombres = base['camaras_ordenadas']
    cams = [camaras[n] for n in nombres]
    if base['aceptados'] < 3:
        raise ValueError('Se requieren al menos 3 puntos triangulados para ajustar')
    ids = base['ids']
    obs = []
    for nuevo_id, original_id in enumerate(ids):
        track = tracks[original_id]
        for cam_id, nombre in enumerate(nombres):
            if nombre in track:
                xy = puntos_por_imagen[nombre][track[nombre]]
                obs.append([cam_id, nuevo_id, *xy])
    if len(obs) < 4:
        raise ValueError('Observaciones insuficientes')
    fit = ajustar(cams, obs, base['puntos'], max_nfev=max_nfev, umbral_px=umbral_px)
    if not np.isfinite(fit['rms_final_px']):
        raise ValueError('Error de ajuste no finito')
    fit['ids_tracks'] = ids
    fit['camaras_ordenadas'] = nombres
    fit['puntos_iniciales'] = base['aceptados']
    fit['tracks_rechazados'] = base['rechazados'] + base['tracks_descartados_entrada']
    fit['advertencia'] += ' Las primeras dos cámaras se mantienen fijas; verificar calibración y escala.'
    return fit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('entrada', type=Path)
    parser.add_argument('--salida', required=True, type=Path)
    parser.add_argument('--umbral-px', type=float, default=3.0)
    args = parser.parse_args()
    datos = json.loads(args.entrada.read_text(encoding='utf-8'))
    r = reconstruir_y_ajustar(datos['camaras'], datos['puntos_por_imagen'], datos['tracks'], args.umbral_px)
    args.salida.mkdir(parents=True, exist_ok=True)
    guardar_ply(r['puntos'], args.salida / 'nube_ajustada.ply')
    (args.salida / 'informe.json').write_text(json.dumps({k:v for k,v in r.items() if k != 'puntos'}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
