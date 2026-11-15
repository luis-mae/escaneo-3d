"""Diagnóstico verificable de una reconstrucción dispersa COLMAP.

Uso: python -m tools.diagnostico_sparse ruta/al/sparse/0
Solo lee images.bin y points3D.bin; no modifica los resultados.
"""
import argparse
import json
import math
import struct
from pathlib import Path


def _read(f, fmt):
    size = struct.calcsize("<" + fmt)
    data = f.read(size)
    if len(data) != size:
        raise ValueError("Archivo COLMAP truncado")
    return struct.unpack("<" + fmt, data)


def _images(path):
    with path.open("rb") as f:
        count, = _read(f, "Q")
        if count > 1_000_000:
            raise ValueError("Cantidad de imágenes inverosímil")
        names = []
        for _ in range(count):
            _read(f, "I7dI")  # image_id, quaternion, translation, camera_id
            raw = bytearray()
            while True:
                char = f.read(1)
                if not char:
                    raise ValueError("Nombre de imagen truncado")
                if char == bytes([0]):
                    break
                raw.extend(char)
                if len(raw) > 4096:
                    raise ValueError("Nombre de imagen demasiado largo")
            names.append(raw.decode("utf-8", errors="replace"))
            n, = _read(f, "Q")
            if n > 100_000_000:
                raise ValueError("Cantidad de observaciones inverosímil")
            f.seek(n * 24, 1)  # x,y,point3D_id
        return names


def _points(path):
    with path.open("rb") as f:
        count, = _read(f, "Q")
        if count > 100_000_000:
            raise ValueError("Cantidad de puntos inverosímil")
        errors, tracks = [], []
        for _ in range(count):
            values = _read(f, "Q3d3Bd")
            error = values[-1]
            n, = _read(f, "Q")
            if n > 100_000_000:
                raise ValueError("Track inverosímil")
            f.seek(n * 8, 1)  # image_id, point2D_idx
            if math.isfinite(error):
                errors.append(error)
            tracks.append(n)
        return count, errors, tracks


def diagnosticar(carpeta):
    carpeta = Path(carpeta)
    names = _images(carpeta / "images.bin")
    count, errors, tracks = _points(carpeta / "points3D.bin")
    return {
        "imagenes_registradas": len(names),
        "nombres_imagenes": names,
        "puntos_3d": count,
        "longitud_track_media": round(sum(tracks) / len(tracks), 3) if tracks else None,
        "error_reproyeccion_medio": round(sum(errors) / len(errors), 4) if errors else None,
        "advertencia": "La cantidad de puntos no demuestra que el objeto sea reconocible; inspeccionar geometría y fondo."
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("carpeta", help="Carpeta sparse/0 de COLMAP")
    parser.add_argument("--salida", help="Archivo JSON opcional")
    args = parser.parse_args()
    result = diagnosticar(args.carpeta)
    output = json.dumps(result, indent=2, ensure_ascii=False)
    if args.salida:
        Path(args.salida).write_text(output + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
