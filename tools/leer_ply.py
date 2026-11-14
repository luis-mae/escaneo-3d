"""Lectura segura de nubes PLY ASCII XYZ para reutilizar exportaciones."""
import argparse
import json
import math
from pathlib import Path

import numpy as np


def leer_ply_xyz(ruta, max_puntos=2_000_000):
    if type(max_puntos) is not int or max_puntos < 1:
        raise ValueError("Límite de puntos inválido")
    ruta = Path(ruta)
    with ruta.open("r", encoding="ascii") as f:
        if f.readline().strip() != "ply" or f.readline().strip() != "format ascii 1.0":
            raise ValueError("PLY ASCII 1.0 requerido")
        cabecera = []
        for _ in range(128):
            linea = f.readline()
            if not linea:
                raise ValueError("Cabecera PLY truncada")
            if linea.strip() == "end_header":
                break
            cabecera.append(linea.strip())
        else:
            raise ValueError("Cabecera PLY demasiado extensa")
        elementos = [l for l in cabecera if l.startswith("element ")]
        if len(elementos) != 1 or len(elementos[0].split()) != 3 or not elementos[0].startswith("element vertex "):
            raise ValueError("Solo se admiten vértices XYZ, sin caras")
        try:
            cantidad = int(elementos[0].split()[2])
        except ValueError as e:
            raise ValueError("Cantidad de vértices inválida") from e
        if not 0 < cantidad <= max_puntos:
            raise ValueError("Cantidad de vértices fuera del límite")
        if any(not l.startswith(("element ", "property ", "comment ", "obj_info ")) for l in cabecera):
            raise ValueError("Directiva PLY no admitida")
        propiedades = [l for l in cabecera if l.startswith("property ")]
        if propiedades != ["property float x", "property float y", "property float z"]:
            raise ValueError("Propiedades XYZ incompatibles")
        puntos = np.empty((cantidad, 3), dtype=float)
        for i in range(cantidad):
            linea = f.readline()
            if not linea:
                raise ValueError("PLY truncado")
            partes = linea.split()
            if len(partes) != 3:
                raise ValueError("Fila XYZ inválida")
            try:
                valores = [float(x) for x in partes]
            except ValueError as e:
                raise ValueError("Coordenadas inválidas") from e
            if not all(math.isfinite(x) for x in valores):
                raise ValueError("Coordenadas no finitas")
            puntos[i] = valores
        if f.read(1):
            raise ValueError("Contenido adicional después de vértices")
    return puntos


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("entrada", type=Path)
    p.add_argument("--max-puntos", type=int, default=2_000_000)
    args = p.parse_args()
    puntos = leer_ply_xyz(args.entrada, args.max_puntos)
    print(json.dumps({"estado": "leido", "puntos": len(puntos),
                      "minimo": puntos.min(axis=0).tolist(),
                      "maximo": puntos.max(axis=0).tolist()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
