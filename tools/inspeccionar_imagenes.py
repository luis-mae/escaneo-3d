"""Inspección rápida de dimensiones y firmas; no decodifica ni evalúa nitidez."""
import argparse
import json
import struct
from pathlib import Path


def dimensiones(path: Path):
    with path.open('rb') as f:
        data = f.read(1024 * 1024)
    if data.startswith(b'\x89PNG\r\n\x1a\n') and len(data) >= 24 and data[12:16] == b'IHDR':
        return struct.unpack('>II', data[16:24])
    if data[:2] == b'\xff\xd8':
        i = 2
        while i + 4 <= len(data):
            if data[i] != 0xff:
                i += 1
                continue
            while i < len(data) and data[i] == 0xff:
                i += 1
            if i >= len(data):
                break
            marker = data[i]
            i += 1
            if marker in (0xd8, 0xd9) or 0xd0 <= marker <= 0xd7:
                continue
            if i + 2 > len(data):
                break
            length = int.from_bytes(data[i:i+2], 'big')
            if length < 2 or i + length > len(data):
                break
            if marker in (0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf) and length >= 7:
                h = int.from_bytes(data[i+3:i+5], 'big')
                w = int.from_bytes(data[i+5:i+7], 'big')
                return (w, h)
            i += length
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP' and data[12:16] == b'VP8X' and len(data) >= 30:
        return (1 + int.from_bytes(data[24:27], 'little'), 1 + int.from_bytes(data[27:30], 'little'))
    return None


def inspeccionar(carpeta: Path, minimo_lado: int = 720):
    if not carpeta.is_dir():
        raise FileNotFoundError(carpeta)
    resultado = []
    for p in sorted(carpeta.iterdir()):
        if not p.is_file() or p.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.webp', '.heic'}:
            continue
        dims = dimensiones(p)
        resultado.append({'archivo': p.name, 'dimensiones': list(dims) if dims else None,
                          'estado': 'no_verificable' if dims is None else ('resolucion_baja' if min(dims) < minimo_lado else 'resolucion_aceptable')})
    return {'imagenes': resultado, 'advertencia': 'La firma y las dimensiones no garantizan una imagen decodificable ni adecuada para reconstrucción.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('carpeta', type=Path)
    parser.add_argument('--minimo-lado', type=int, default=720)
    args = parser.parse_args()
    print(json.dumps(inspeccionar(args.carpeta, args.minimo_lado), ensure_ascii=False, indent=2))
