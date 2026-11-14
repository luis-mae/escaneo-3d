"""Fusión de nubes prealineadas con correspondencias geométricas recíprocas.

Solo apta para nubes aproximadamente en un mismo marco y escala.
No hace registro global ni recupera escala métrica.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from .correspondencias_3d import correspondencias_mutuas
from .fusion_robusta import fusionar
from .nube_dos_vistas import guardar_ply


def fusionar_prealineadas(nubes, radio, umbral, voxel=0.0, minimo=3, semilla=0):
    if not isinstance(nubes, (list, tuple)) or len(nubes) < 2:
        raise ValueError("Se requieren al menos dos nubes")
    base = np.asarray(nubes[0], dtype=float)
    if base.ndim != 2 or base.shape[1] != 3 or not len(base) or not np.isfinite(base).all():
        raise ValueError("Nube base inválida")
    if not np.isfinite(umbral) or umbral <= 0:
        raise ValueError("Umbral inválido")
    referencias = []
    estadisticas = []
    for nube in nubes[1:]:
        # La similitud se estima desde la nube posterior hacia la base.
        # Por tanto, origen = nube posterior, destino = base.
        pares = correspondencias_mutuas(nube, base, radio, minimo)
        referencias.append({"origen": pares["origen"], "destino": pares["destino"]})
        estadisticas.append({"pares_reciprocos": pares["cantidad"],
                             "distancia_media": float(np.mean(pares["distancias"]))})
    puntos, informe = fusionar(nubes, referencias, umbral=umbral, voxel=voxel, semilla=semilla)
    informe["emparejamientos"] = estadisticas
    informe["modo"] = "prealineado_reciproco"
    informe["advertencia"] = (
        "Solo para nubes previamente alineadas y con escala comparable. "
        "Vecindad geométrica no garantiza homología física ni precisión métrica."
    )
    return puntos, informe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entrada", type=Path, help="JSON con nubes: [Nx3, Nx3, ...]")
    parser.add_argument("--salida", type=Path, required=True)
    parser.add_argument("--radio", type=float, required=True)
    parser.add_argument("--umbral", type=float, required=True)
    parser.add_argument("--voxel", type=float, default=0.0)
    args = parser.parse_args()
    data = json.loads(args.entrada.read_text(encoding="utf-8"))
    puntos, informe = fusionar_prealineadas(data["nubes"], args.radio, args.umbral, args.voxel)
    args.salida.mkdir(parents=True, exist_ok=True)
    guardar_ply(puntos, args.salida / "fusion.ply")
    (args.salida / "informe_fusion.json").write_text(
        json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
