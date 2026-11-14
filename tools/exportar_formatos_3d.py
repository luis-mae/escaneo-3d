"""Exporta una malla OBJ triangular a OBJ, PLY ASCII, STL, GLB 2.0 y 3MF Core.

La geometría se conserva; las unidades de origen siguen sin certificar.
"""
import argparse
import hashlib
import json
import struct
import shutil
import zipfile
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


def escribir_glb_malla(ruta, vertices, caras):
    """Escribe un GLB 2.0 autocontenido con posiciones e índices triangulares."""
    v, f = _validar(vertices, caras)
    posiciones = np.asarray(v, dtype="<f4")
    indices = np.asarray(f, dtype="<u4").reshape(-1)
    if not np.isfinite(posiciones).all():
        raise ValueError("Las coordenadas exceden el rango GLB float32")
    bytes_posiciones = posiciones.tobytes(order="C")
    bytes_indices = indices.tobytes(order="C")
    offset_indices = (len(bytes_posiciones) + 3) // 4 * 4
    binario = bytes_posiciones + b"\x00" * (offset_indices - len(bytes_posiciones)) + bytes_indices
    documento = {
        "asset": {"version": "2.0", "generator": "ESCANEO 3D"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{
            "attributes": {"POSITION": 0},
            "indices": 1,
            "mode": 4
        }]}],
        "buffers": [{"byteLength": len(binario)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(bytes_posiciones), "target": 34962},
            {"buffer": 0, "byteOffset": offset_indices, "byteLength": len(bytes_indices), "target": 34963}
        ],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": len(v), "type": "VEC3",
             "min": posiciones.min(axis=0).astype(float).tolist(),
             "max": posiciones.max(axis=0).astype(float).tolist()},
            {"bufferView": 1, "componentType": 5125, "count": len(indices), "type": "SCALAR",
             "min": [int(indices.min())], "max": [int(indices.max())]}
        ]
    }
    json_chunk = json.dumps(documento, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    json_chunk += b" " * ((4 - len(json_chunk) % 4) % 4)
    binario += b"\x00" * ((4 - len(binario) % 4) % 4)
    longitud = 12 + 8 + len(json_chunk) + 8 + len(binario)
    with Path(ruta).open("wb") as archivo:
        archivo.write(struct.pack("<4sII", b"glTF", 2, longitud))
        archivo.write(struct.pack("<II", len(json_chunk), 0x4E4F534A))
        archivo.write(json_chunk)
        archivo.write(struct.pack("<II", len(binario), 0x004E4942))
        archivo.write(binario)


def escribir_3mf_malla(ruta, vertices, caras):
    """Escribe un paquete 3MF Core con una malla triangular; unidad asumida mm."""
    v, f = _validar(vertices, caras)
    lineas_vertices = "".join(
        f'<vertex x="{x:.9g}" y="{y:.9g}" z="{z:.9g}"/>'
        for x, y, z in v
    )
    lineas_caras = "".join(
        f'<triangle v1="{a}" v2="{b}" v3="{c}"/>'
        for a, b, c in f
    )
    modelo = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<model unit="millimeter" xml:lang="es" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
        '<metadata name="Title">ESCANEO 3D</metadata>'
        '<metadata name="Description">Unidad asumida mm; escala física no calibrada.</metadata>'
        '<resources><object id="1" type="model"><mesh><vertices>'
        + lineas_vertices
        + '</vertices><triangles>'
        + lineas_caras
        + '</triangles></mesh></object></resources>'
        '<build><item objectid="1"/></build></model>'
    )
    tipos = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
        '</Types>'
    )
    relaciones = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
        'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
        '</Relationships>'
    )
    with zipfile.ZipFile(ruta, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as paquete:
        paquete.writestr("[Content_Types].xml", tipos)
        paquete.writestr("_rels/.rels", relaciones)
        paquete.writestr("3D/3dmodel.model", modelo)


def exportar_formatos(entrada, carpeta_salida, formatos=("obj", "ply", "stl")):
    origen = Path(entrada).resolve()
    carpeta = Path(carpeta_salida).resolve()
    formatos = tuple(dict.fromkeys(str(x).lower() for x in formatos))
    if not formatos or any(x not in ("obj", "ply", "stl", "glb", "3mf") for x in formatos):
        raise ValueError("Formatos admitidos: obj, ply, stl, glb, 3mf")
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
            elif extension == "stl":
                escribir_stl_malla(destino, v, f)
            elif extension == "glb":
                escribir_glb_malla(destino, v, f)
            else:
                escribir_3mf_malla(destino, v, f)
            archivos.append({"archivo": destino.name,
                             "bytes": destino.stat().st_size,
                             "sha256": hashlib.sha256(destino.read_bytes()).hexdigest()})
        informe = {"entrada": str(origen), "vertices": len(v), "caras": len(f),
                   "archivos": archivos,
                   "advertencia": "Las unidades y la precisión no están verificadas. GLB no define unidades físicas; 3MF asume milímetros sin calibrar; STL no implica que la malla sea imprimible."}
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
