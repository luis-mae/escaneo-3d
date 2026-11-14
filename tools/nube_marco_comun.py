"""Triangulación multivista en un marco común con cámaras EXTRÍNSECAS conocidas.

No estima poses a partir de fotos: exige matrices world->camera calibradas.
Escala determinada por las traslaciones de entrada; no asumir milímetros.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from tools.nube_dos_vistas import guardar_ply


def reconstruir_observaciones(camaras, pistas, umbral_px=2.0, min_vistas=2):
    """camaras: [{K:3x3,R:3x3,t:3}], pistas: [{id,observaciones:[{camara,xy}]}]."""
    if len(camaras) < 2 or min_vistas < 2 or not np.isfinite(umbral_px) or umbral_px <= 0:
        raise ValueError('Configuración inválida')
    proyecciones = []
    for c in camaras:
        K, R, t = (np.asarray(c[k], dtype=float) for k in ('K', 'R', 't'))
        if K.shape != (3, 3) or R.shape != (3, 3) or t.size != 3 or not all(np.isfinite(x).all() for x in (K,R,t)):
            raise ValueError('Cámara inválida')
        if abs(np.linalg.det(K)) < 1e-10 or not np.allclose(R @ R.T, np.eye(3), atol=1e-3) or np.linalg.det(R) < 0.99:
            raise ValueError('Calibración inválida')
        proyecciones.append((K, R, t.reshape(3), K @ np.column_stack((R, t.reshape(3)))))
    puntos, ids, rechazados = [], [], 0
    for pista in pistas:
        obs = pista.get('observaciones', [])
        indices = [o.get('camara') for o in obs]
        if len(obs) < min_vistas or len(set(indices)) != len(indices) or any(not isinstance(i,int) or i < 0 or i >= len(camaras) for i in indices):
            rechazados += 1; continue
        A = []
        valido = True
        for o in obs:
            xy = np.asarray(o.get('xy'), dtype=float)
            if xy.shape != (2,) or not np.isfinite(xy).all():
                valido = False; break
            P = proyecciones[o['camara']][3]
            A.extend([xy[0] * P[2] - P[0], xy[1] * P[2] - P[1]])
        if not valido:
            rechazados += 1; continue
        _, s, vh = np.linalg.svd(np.asarray(A))
        Xh = vh[-1]
        if abs(Xh[3]) < 1e-10:
            rechazados += 1; continue
        X = Xh[:3] / Xh[3]
        errores = []
        for o in obs:
            K, R, t, P = proyecciones[o['camara']]
            z = (R @ X + t)[2]
            if z <= 1e-8:
                valido = False; break
            proyectado = P @ np.r_[X, 1.0]
            errores.append(np.linalg.norm(proyectado[:2] / proyectado[2] - o['xy']))
        if not valido or max(errores) > umbral_px:
            rechazados += 1; continue
        puntos.append(X.tolist()); ids.append(pista.get('id', len(ids)))
    return {'estado': 'experimental', 'puntos': puntos, 'ids': ids, 'aceptados': len(puntos),
            'rechazados': rechazados, 'marco': 'comun', 'escala': 'unidades_de_traslacion_de_camara',
            'advertencia': 'Requiere poses globales calibradas. No estima poses ni garantiza modelo imprimible.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('entrada', type=Path, help='JSON con camaras y pistas')
    p.add_argument('--salida', type=Path, required=True)
    p.add_argument('--umbral-px', type=float, default=2.0)
    args = p.parse_args()
    datos = json.loads(args.entrada.read_text(encoding='utf-8'))
    r = reconstruir_observaciones(datos['camaras'], datos['pistas'], args.umbral_px)
    args.salida.mkdir(parents=True, exist_ok=True)
    guardar_ply(r['puntos'], args.salida / 'nube_comun.ply')
    (args.salida / 'informe.json').write_text(json.dumps({k:v for k,v in r.items() if k != 'puntos'}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f"Puntos aceptados: {r['aceptados']}; rechazados: {r['rechazados']}")

if __name__ == '__main__':
    main()
