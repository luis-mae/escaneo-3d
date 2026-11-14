"""Exporta una malla OBJ triangular a OBJ, PLY ASCII y STL binario.

La geometría se conserva; las unidades de origen siguen sin certificar.
"""
import argparse
import hashlib
import json
import struct
import shutil
from pathlib import Path

import numpy as np

from .reparar_malla import leer_obj_triangulos


def _validar(vertices, caras):
    v = np.asarray(vertices, dtype=float)
    f = np.asarray(caras, dtype=int)
    if v.ndim != 2 or v.shape[1] != 3 or not len(v) or not np.isfinite(v).all():
        raise ValueError("Vértices inválidos")
    if f.ndim != 2 or f.shape[1] != 3 or not len(f) or f.min() < 0 or f.max() >= len(v):
        raise ValueError("Caras inválidas")
    if any(len(set(map(int, cara))) != 3 for cara in f):
        raise ValueError("Caras degeneradas por índices repetidos")
    return v, f


def escribir_ply_malla(ruta, vertices, caras):
    v, f = _validar(vertices, caras)
    with Path(ruta).open("w", encoding="ascii", newline="\n") as archivo:
        archivo.write("ply\nformat ascii 1.0\n")
        archivo.write(f"element vertex {len(v)}\n")
        archivo.write("property double x\nproperty double y\nproperty double z\n")
        archivo.write(f"element face {len(f)}\n")
        archivo.write("property list uchar int vertex_indices\nend_header\n")
        for x, y, z in v:
            archivo.write(f"{x:.17g} {y:.17g} {z:.17g}\n")
        for a, b, c in f:
            archivo.write(f"3 {a} {b} {c}\n")


def escribir_stl_malla(ruta, vertices, caras):
    v, f = _validar(vertices, caras)
    if len(f) > 0xffffffff:
        raise ValueError("Demasiadas caras para STL")
    with Path(ruta).open("wb") as archivo:
        archivo.write(b"Escaneo3D STL; unidades no verificadas".ljust(80, b" "))
        archivo.write(struct.pack("<I", len(f)))
        for a, b, c in f:
            p, q, r = v[[a, b, c]]
            normal = np.cross(q - p, r - p)
            magnitud = np.linalg.norm(normal)
            if magnitud <= 1e-12:
                raise ValueError("Cara degenerada: no se puede exportar STL")
            normal /= magnitud
            valores = np.concatenate((normal, p, q, r))
            if not np.isfinite(valores.astype(np.float32)).all():
                raise ValueError("Coordenadas fuera del rango STL float32")
            archivo.write(struct.pack("<12fH", *valores.tolist(), 0))


def exportar_formatos(entrada, carpeta_salida, formatos=("obj", "ply", "stl")):
    origen = Path(entrada).resolve()
    carpeta = Path(carpeta_salida).resolve()
    formatos = tuple(dict.fromkeys(str(x).lower() for x in formatos))
    if not formatos or any(x not in ("obj", "ply", "stl") for x in formatos):
        raise ValueError("Formatos admitidos: obj, ply, stl")
    if not origen.is_file() or origen.suffix.lower() != ".obj":
        raise ValueError("Se requiere OBJ de entrada")
    if carpeta.exists():
        raise FileExistsError("La carpeta de exportación ya existe; no sobrescribir")
    if carpeta == origen.parent or carpeta in origen.parents:
        raise ValueError("La carpeta de salida debe estar separada")
    v, f = _validar(*leer_obj_triangulos(origen))
    carpeta.mkdir(parents=True)
    try:
        archivos = []
        for extension in formatos:
            destino = carpeta / ("modelo." + extension)
            if extension == "obj":
                with destino.open("w", encoding="utf-8") as salida:
                    salida.write("# ESCANEO 3D; escala no verificada\n")
                    for x, y, z in v:
                        salida.write(f"v {x:.17g} {y:.17g} {z:.17g}\n")
                    for a, b, c in f:
                        salida.write(f"f {a+1} {b+1} {c+1}\n")
            elif extension == "ply":
                escribir_ply_malla(destino, v, f)
            else:
                escribir_stl_malla(destino, v, f)
            archivos.append({"archivo": destino.name,
                             "bytes": destino.stat().st_size,
                             "sha256": hashlib.sha256(destino.read_bytes()).hexdigest()})
        informe = {"entrada": str(origen), "vertices": len(v), "caras": len(f),
                   "archivos": archivos,
                   "advertencia": "Las unidades y la precisión no están verificadas. STL no implica que la malla sea imprimible."}
        (carpeta / "informe_exportacion.json").write_text(
            json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return informe
    except Exception:
        shutil.rmtree(carpeta, ignore_errors=True)
        raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("entrada", type=Path)
    p.add_argument("--salida", type=Path, required=True, help="Carpeta nueva")
    p.add_argument("--formatos", nargs="+", default=["obj", "ply", "stl"])
    args = p.parse_args()
    print(json.dumps(exportar_formatos(args.entrada, args.salida, args.formatos),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
