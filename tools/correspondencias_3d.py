"""Correspondencias 3D automáticas conservadoras entre nubes PREALINEADAS.

Busca vecinos más próximos recíprocos dentro de un radio explícito.
No resuelve rotaciones, traslaciones o escalas grandes; no debe usarse
como sustituto de descriptores visuales ni de registro global.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree


def correspondencias_mutuas(origen, destino, radio, minimo=3):
    """Devuelve pares XYZ con índices únicos y distancia <= radio.

    origen y destino deben estar aproximadamente en el mismo marco y escala.
    """
    a = np.asarray(origen, dtype=float)
    b = np.asarray(destino, dtype=float)
    for nube in (a, b):
        if nube.ndim != 2 or nube.shape[1] != 3 or not len(nube):
            raise ValueError("Se requieren nubes Nx3 no vacías")
        if not np.isfinite(nube).all():
            raise ValueError("Coordenadas no finitas")
    if not np.isfinite(radio) or radio <= 0:
        raise ValueError("Radio debe ser positivo y finito")
    if isinstance(minimo, bool) or not isinstance(minimo, int) or minimo < 3:
        raise ValueError("Mínimo debe ser entero >= 3")
    da, ia = cKDTree(b).query(a, k=1, distance_upper_bound=radio)
    _, ib = cKDTree(a).query(b, k=1, distance_upper_bound=radio)
    indices_a = np.arange(len(a))
    validos = np.isfinite(da) & (ia < len(b))
    indices_a = indices_a[validos]
    indices_b = ia[validos]
    mutuos = ib[indices_b] == indices_a
    indices_a, indices_b = indices_a[mutuos], indices_b[mutuos]
    if len(indices_a) < minimo:
        raise ValueError("Correspondencias recíprocas insuficientes: nubes posiblemente desalineadas")
    distancias = np.linalg.norm(a[indices_a] - b[indices_b], axis=1)
    return {
        "origen": a[indices_a].tolist(),
        "destino": b[indices_b].tolist(),
        "indices_origen": indices_a.tolist(),
        "indices_destino": indices_b.tolist(),
        "distancias": distancias.tolist(),
        "cantidad": int(len(indices_a)),
        "radio": float(radio),
        "advertencia": "Emparejamiento geométrico de nubes prealineadas; no prueba identidad de puntos ni escala métrica."
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entrada", type=Path, help="JSON con origen y destino como listas Nx3")
    parser.add_argument("--salida", type=Path, required=True)
    parser.add_argument("--radio", type=float, required=True)
    parser.add_argument("--minimo", type=int, default=3)
    args = parser.parse_args()
    datos = json.loads(args.entrada.read_text(encoding="utf-8"))
    resultado = correspondencias_mutuas(datos["origen"], datos["destino"], args.radio, args.minimo)
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{resultado['cantidad']} pares recíprocos")


if __name__ == "__main__":
    main()
