"""Auditoría rápida y reproducible de los archivos exportados por ESCANEO 3D.

Comprueba existencia, tamaños y firmas de archivo sin confundir un archivo
válido con una reconstrucción geométricamente fiel.
"""
import argparse
import json
import struct
from pathlib import Path


def auditar_exportaciones(carpeta):
    raiz = Path(carpeta).resolve()
    if not raiz.is_dir():
        raise ValueError("No existe la carpeta de exportaciones")
    resultados = {}
    for ext in ("obj", "stl", "glb"):
        ruta = raiz / ("modelo." + ext)
        estado = {"existe": ruta.is_file(), "valido_basico": False}
        if ruta.is_file():
            tam = ruta.stat().st_size
            estado["bytes"] = tam
            with ruta.open("rb") as f:
                cabecera = f.read(84)
            if ext == "glb":
                estado["valido_basico"] = (
                    tam >= 28 and cabecera[:4] == b"glTF"
                    and struct.unpack_from("<I", cabecera, 4)[0] == 2
                    and struct.unpack_from("<I", cabecera, 8)[0] == tam
                )
                if estado["valido_basico"]:
                    try:
                        with ruta.open("rb") as archivo:
                            archivo.seek(12)
                            longitud_json, tipo_json = struct.unpack("<II", archivo.read(8))
                            if (tipo_json != 0x4E4F534A or longitud_json % 4\n                                    or longitud_json < 4\n                                    or longitud_json > tam - 28):
                                raise ValueError("GLB JSON chunk inválido")
                            documento = json.loads(archivo.read(longitud_json))
                            longitud_bin, tipo_bin = struct.unpack("<II", archivo.read(8))
                            estado["valido_basico"] = (
                                tipo_bin == 0x004E4942 and longitud_bin % 4 == 0
                                and 12 + 8 + longitud_json + 8 + longitud_bin == tam
                                and isinstance(documento, dict)
                                and documento.get("asset", {}).get("version") == "2.0"
                            )
                    except (OSError, ValueError, UnicodeError, struct.error, TypeError):
                        estado["valido_basico"] = False
            elif ext == "stl":
                estado["valido_basico"] = (
                    tam >= 84 and tam == 84 + 50 * struct.unpack_from("<I", cabecera, 80)[0]
                    and struct.unpack_from("<I", cabecera, 80)[0] > 0
                )
            else:
                try:
                    from math import isfinite
                    n_vertices = 0
                    n_caras = 0
                    indices_validos = True
                    with ruta.open("r", encoding="utf-8") as archivo:
                        for linea in archivo:
                            partes = linea.strip().split()
                            if not partes or partes[0].startswith("#"):
                                continue
                            if partes[0] == "v":
                                if len(partes) != 4:
                                    indices_validos = False
                                    break
                                xyz = [float(x) for x in partes[1:]]
                                if not all(isfinite(x) for x in xyz):
                                    indices_validos = False
                                    break
                                n_vertices += 1
                            elif partes[0] == "f":
                                if len(partes) != 4:
                                    indices_validos = False
                                    break
                                indices = [int(x.split("/")[0]) for x in partes[1:]]
                                if (len(set(indices)) != 3
                                        or any(i <= 0 or i > n_vertices for i in indices)):
                                    indices_validos = False
                                    break
                                n_caras += 1
                    estado["valido_basico"] = (
                        indices_validos and n_vertices >= 3 and n_caras > 0
                    )
                except (OSError, UnicodeError, ValueError, OverflowError):
                    pass
        resultados[ext] = estado
    return {
        "archivos": resultados,
        "exportaciones_validas_basicas": all(
            item["valido_basico"] for item in resultados.values()
        ),
        "geometria_validada": False,
        "escala_validada": False,
        "advertencia": "Las firmas de archivo no prueban fidelidad del objeto ni imprimibilidad.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("carpeta", type=Path, help="Carpeta que contiene modelo.obj, modelo.stl y modelo.glb")
    args = parser.parse_args()
    reporte = auditar_exportaciones(args.carpeta)
    print(json.dumps(reporte, ensure_ascii=False, indent=2))
    raise SystemExit(0 if reporte["exportaciones_validas_basicas"] else 1)


if __name__ == "__main__":
    main()
