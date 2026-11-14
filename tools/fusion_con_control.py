"""Fusión rígida controlada de nubes prealineadas, con rechazo previo.

Cada nube se registra contra la nube BASE ORIGINAL; nunca se acepta una nube
con cobertura bidireccional inferior al mínimo solicitado. No hay escala libre.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from .registro_con_control import registrar_con_control
from .nube_dos_vistas import guardar_ply


def fusionar_con_control(nubes, radio, cobertura_minima=0.6, voxel=0.0, max_iter=30):
    if not isinstance(nubes, (list, tuple)) or len(nubes) < 2:
        raise ValueError("Se requieren al menos dos nubes")
    if not np.isscalar(voxel) or not np.isfinite(voxel) or voxel < 0:
        raise ValueError("Voxel inválido")
    pts = [np.asarray(p, dtype=float) for p in nubes]
    for p in pts:
        if p.ndim != 2 or p.shape[1] != 3 or len(p) < 3 or not np.isfinite(p).all():
            raise ValueError("Nube Nx3 inválida")
    base = pts[0]
    piezas = [base]
    reportes = []
    for i, nube in enumerate(pts[1:], start=1):
        ajuste = registrar_con_control(nube, base, radio, cobertura_minima, max_iter)
        if not ajuste["aprobado_para_fusion_experimental"]:
            raise ValueError(f"Nube {i} rechazada por cobertura insuficiente; no se exporta fusión")
        rot = np.asarray(ajuste["rotacion"])
        trans = np.asarray(ajuste["traslacion"])
        piezas.append(nube @ rot.T + trans)
        reportes.append({"indice_nube": i, "registro": ajuste})
    fusion = np.concatenate(piezas, axis=0)
    puntos_antes = len(fusion)
    if voxel > 0:
        # Coordenadas relativas: evitan overflow por origen geográfico lejano.
        origen_voxel = fusion.min(axis=0)
        indices = (fusion - origen_voxel) / voxel
        if not np.isfinite(indices).all() or np.max(indices) >= 2**52:
            raise ValueError("Voxel demasiado pequeño para el rango de la nube")
        claves = np.floor(indices).astype(np.int64)
        _, inversos = np.unique(claves, axis=0, return_inverse=True)
        cuentas = np.bincount(inversos)
        acumulados = np.stack(
            [np.bincount(inversos, weights=fusion[:, j]) for j in range(3)], axis=1
        )
        fusion = acumulados / cuentas[:, None]
    return fusion, {
        "estado": "fusion_rigida_controlada_experimental",
        "nubes": len(nubes),
        "puntos_entrada": puntos_antes,
        "puntos_salida": len(fusion),
        "registros": reportes,
        "advertencia": "Exige prealineación, solapamiento y escala común. No certifica exactitud métrica ni reconstrucción fotogramétrica."
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("entrada", type=Path, help="JSON con nubes: lista de Nx3")
    p.add_argument("--salida", type=Path, required=True)
    p.add_argument("--radio", type=float, required=True)
    p.add_argument("--cobertura-minima", type=float, default=0.6)
    p.add_argument("--voxel", type=float, default=0.0)
    args = p.parse_args()
    datos = json.loads(args.entrada.read_text(encoding="utf-8"))
    nube, informe = fusionar_con_control(datos["nubes"], args.radio, args.cobertura_minima, args.voxel)
    args.salida.mkdir(parents=True, exist_ok=True)
    guardar_ply(nube, args.salida / "fusion_controlada.ply")
    (args.salida / "informe_controlado.json").write_text(
        json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
