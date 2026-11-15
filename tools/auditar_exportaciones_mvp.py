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
                    tam >= 20 and cabecera[:4] == b"glTF"
                    and struct.unpack_from("<I", cabecera, 4)[0] == 2
                    and struct.unpack_from("<I", cabecera, 8)[0] == tam
                )
            elif ext == "stl":
                estado["valido_basico"] = (
                    tam >= 84 and tam == 84 + 50 * struct.unpack_from("<I", cabecera, 80)[0]
                    and struct.unpack_from("<I", cabecera, 80)[0] > 0
                )
            else:
                try:
                    with ruta.open("r", encoding="utf-8") as f:
                        lineas = f.read(2_000_000).splitlines()
                    estado["valido_basico"] = (
                        any(x.startswith("v ") for x in lineas)
                        and any(x.startswith("f ") for x in lineas)
                    )
                except (OSError, UnicodeError):
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
