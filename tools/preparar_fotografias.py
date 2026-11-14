"""Prepara copias JPEG orientadas y limitadas en resolución para reconstrucción.

Nunca altera los originales. Requiere Pillow. No reconstruye geometría 3D.
"""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageOps, UnidentifiedImageError

EXTENSIONES = {'.jpg', '.jpeg', '.png', '.webp', '.tif', '.tiff'}


def preparar(origen: Path, destino: Path, max_lado: int = 2048, calidad: int = 90):
    if max_lado < 256 or not 1 <= calidad <= 95:
        raise ValueError('max_lado >= 256 y calidad entre 1 y 95')
    if not origen.is_dir():
        raise NotADirectoryError(origen)
    if origen.resolve() == destino.resolve():
        raise ValueError('La carpeta de destino debe ser distinta del origen')
    destino.mkdir(parents=True, exist_ok=True)
    resultado = []
    for indice, archivo in enumerate(sorted(origen.iterdir())):
        if not archivo.is_file() or archivo.suffix.lower() not in EXTENSIONES:
            continue
        item = {'original': archivo.name}
        try:
            with Image.open(archivo) as img:
                img = ImageOps.exif_transpose(img)
                original = img.size
                img = img.convert('RGB')
                img.thumbnail((max_lado, max_lado), Image.Resampling.LANCZOS)
                salida = f'foto_{indice:04d}.jpg'
                img.save(destino / salida, 'JPEG', quality=calidad, optimize=True)
                item.update({'archivo': salida, 'dimensiones_originales': list(original),
                             'dimensiones_procesadas': list(img.size), 'estado': 'ok'})
        except (OSError, ValueError, UnidentifiedImageError) as exc:
            item.update({'estado': 'error', 'detalle': str(exc)})
        resultado.append(item)
    informe = {'fotografias': resultado, 'total_ok': sum(i['estado'] == 'ok' for i in resultado),
               'advertencia': 'La reducción puede perder detalle. Conservar originales para procesamiento PRO.'}
    (destino / 'manifest.json').write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding='utf-8')
    return informe


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('origen', type=Path)
    p.add_argument('destino', type=Path)
    p.add_argument('--max-lado', type=int, default=2048)
    p.add_argument('--calidad', type=int, default=90)
    a = p.parse_args()
    print(json.dumps(preparar(a.origen, a.destino, a.max_lado, a.calidad), ensure_ascii=False, indent=2))
