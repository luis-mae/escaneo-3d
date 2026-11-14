"""Lector acotado de nubes PLY binarias o ASCII con propiedades adicionales.

Permite conectar fused.ply de COLMAP al generador de superficies existente.
No interpreta caras ni certifica unidades físicas.
"""
import argparse
import json
import math
import random
import struct
from pathlib import Path

import numpy as np

TIPOS = {
    "char": "b", "int8": "b", "uchar": "B", "uint8": "B",
    "short": "h", "int16": "h", "ushort": "H", "uint16": "H",
    "int": "i", "int32": "i", "uint": "I", "uint32": "I",
    "float": "f", "float32": "f", "double": "d", "float64": "d",
}


def leer_nube_colmap_ply(ruta, max_puntos=2_000_000, submuestrear=False):
    """Lee XYZ y opcionalmente reduce nubes grandes mediante muestreo determinista."""
    if type(max_puntos) is not int or max_puntos < 4:
        raise ValueError("max_puntos debe ser entero >= 4")
    ruta = Path(ruta)
    with ruta.open("rb") as f:
        if f.readline().strip() != b"ply":
            raise ValueError("No es un archivo PLY")
        formato = f.readline().decode("ascii", "strict").strip()
        if formato not in ("format binary_little_endian 1.0",
                           "format binary_big_endian 1.0", "format ascii 1.0"):
            raise ValueError("Formato PLY no admitido")
        cantidad = None
        propiedades = []
        elemento = None
        terminado = False
        for _ in range(256):
            linea = f.readline()
            if not linea or len(linea) > 8192:
                raise ValueError("Cabecera PLY truncada o excesiva")
            texto = linea.decode("ascii", "strict").strip()
            if texto == "end_header":
                terminado = True
                break
            partes = texto.split()
            if not partes or partes[0] in ("comment", "obj_info"):
                continue
            if partes[0] == "element" and len(partes) == 3:
                elemento = partes[1]
                if elemento != "vertex":
                    raise ValueError("Solo se admiten nubes PLY sin caras")
                if cantidad is not None:
                    raise ValueError("Elemento vertex duplicado")
                try:
                    cantidad = int(partes[2])
                except ValueError as exc:
                    raise ValueError("Cantidad de vértices inválida") from exc
            elif partes[0] == "property" and len(partes) == 3 and elemento == "vertex":
                if partes[1] not in TIPOS:
                    raise ValueError("Tipo de propiedad PLY no admitido")
                propiedades.append((partes[2], TIPOS[partes[1]]))
            else:
                raise ValueError("Directiva PLY no admitida")
        if not terminado or cantidad is None or cantidad < 4 or cantidad > 50_000_000:
            raise ValueError("Cabecera o cantidad de vértices inválida")
        if cantidad > max_puntos and not submuestrear:
            raise ValueError("Cantidad de vértices fuera del límite")
        nombres = [p[0] for p in propiedades]
        if len(nombres) != len(set(nombres)) or not all(
            nombres.count(n) == 1 for n in ("x", "y", "z")
        ):
            raise ValueError("Se requieren propiedades XYZ únicas")
        indices = [nombres.index(n) for n in ("x", "y", "z")]
        limite = min(cantidad, max_puntos)
        puntos = np.empty((limite, 3), dtype=np.float64)
        rng = random.Random(0)
        guardados = 0
        if formato.startswith("format binary"):
            prefijo = "<" if "little" in formato else ">"
            registro = struct.Struct(prefijo + "".join(t for _, t in propiedades))
            for i in range(cantidad):
                datos = f.read(registro.size)
                if len(datos) != registro.size:
                    raise ValueError("PLY binario truncado")
                valores = registro.unpack(datos)
                xyz = [valores[j] for j in indices]
                if i < limite:
                    puntos[i] = xyz
                    guardados += 1
                elif submuestrear:
                    elegido = rng.randint(0, i)
                    if elegido < limite:
                        puntos[elegido] = xyz
        else:
            for i in range(cantidad):
                linea = f.readline()
                if not linea:
                    raise ValueError("PLY ASCII truncado")
                partes = linea.split()
                if len(partes) != len(propiedades):
                    raise ValueError("Fila PLY inválida")
                try:
                    xyz = [float(partes[j]) for j in indices]
                except ValueError as exc:
                    raise ValueError("Coordenadas PLY inválidas") from exc
                if i < limite:
                    puntos[i] = xyz
                    guardados += 1
                elif submuestrear:
                    elegido = rng.randint(0, i)
                    if elegido < limite:
                        puntos[elegido] = xyz
        if f.read(1):
            raise ValueError("Datos adicionales al final del PLY")
    puntos = puntos[:guardados]
    if not np.isfinite(puntos).all():
        raise ValueError("Coordenadas no finitas")
    return puntos


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("entrada", type=Path)
    p.add_argument("--max-puntos", type=int, default=2_000_000)
    args = p.parse_args()
    puntos = leer_nube_colmap_ply(args.entrada, args.max_puntos)
    print(json.dumps({"puntos": len(puntos), "min": puntos.min(axis=0).tolist(),
                      "max": puntos.max(axis=0).tolist()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
