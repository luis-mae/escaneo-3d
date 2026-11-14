"""Fusiona nubes Nx3 usando correspondencias 3D explícitas y RANSAC Sim(3).

No descubre correspondencias automáticamente. Las coordenadas resultantes siguen
siendo relativas salvo calibración métrica independiente.
"""
import argparse
import json
from pathlib import Path
import numpy as np

try:
    from .registrar_escala_robusta import estimar_similitud_robusta
    from .registrar_escala import transformar_puntos
    from .nube_dos_vistas import guardar_ply
except ImportError:
    from registrar_escala_robusta import estimar_similitud_robusta
    from registrar_escala import transformar_puntos
    from nube_dos_vistas import guardar_ply


def fusionar(nubes, correspondencias, umbral=0.05, voxel=0.0, semilla=0):
    """Nubes [base, segunda, ...], referencias por nube posterior en marco base.

    correspondencias: [{origen: Nx3, destino: Nx3}, ...].
    """
    if len(nubes) < 2 or len(correspondencias) != len(nubes) - 1:
        raise ValueError('Cantidad de nubes/correspondencias inválida')
    if not np.isfinite(voxel) or voxel < 0:
        raise ValueError('Voxel inválido')
    piezas = []
    ajustes = []
    for indice, nube in enumerate(nubes):
        pts = np.asarray(nube, float)
        if pts.ndim != 2 or pts.shape[1] != 3 or not len(pts) or not np.isfinite(pts).all():
            raise ValueError('Nube inválida')
        if indice:
            refs = correspondencias[indice - 1]
            ajuste = estimar_similitud_robusta(refs['origen'], refs['destino'], umbral, semilla=semilla)
            pts = transformar_puntos(pts, ajuste)
            ajustes.append(ajuste)
        piezas.append(pts)
    fusion = np.concatenate(piezas, axis=0)
    antes = len(fusion)
    if voxel > 0:
        # Promedio por voxel; evita sesgo hacia el primer punto encontrado.
        claves = np.rint(fusion / voxel).astype(np.int64)
        _, inversos = np.unique(claves, axis=0, return_inverse=True)
        cuentas = np.bincount(inversos)
        acumulados = np.stack([np.bincount(inversos, weights=fusion[:, j]) for j in range(3)], axis=1)
        fusion = acumulados / cuentas[:, None]
    return fusion, {'estado': 'fusion_relativa_experimental', 'nubes': len(nubes),
                   'puntos_entrada': antes, 'puntos_salida': len(fusion),
                   'ajustes': ajustes,
                   'advertencia': 'Requiere correspondencias 3D suministradas. No demuestra precisión métrica.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('entrada', type=Path, help='JSON: nubes (listas Nx3), correspondencias')
    p.add_argument('--salida', type=Path, required=True)
    p.add_argument('--umbral', type=float, default=0.05)
    p.add_argument('--voxel', type=float, default=0.0)
    args = p.parse_args()
    data = json.loads(args.entrada.read_text(encoding='utf-8'))
    nube, reporte = fusionar(data['nubes'], data['correspondencias'], args.umbral, args.voxel)
    args.salida.mkdir(parents=True, exist_ok=True)
    guardar_ply(nube, args.salida / 'fusion.ply')
    (args.salida / 'informe_fusion.json').write_text(json.dumps(reporte, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in reporte.items() if k != 'ajustes'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
