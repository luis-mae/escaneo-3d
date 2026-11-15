"""Eliminación opcional de fondo para fotogrametría, sin requerir GPU.

Instalación: python -m pip install "rembg[cpu]" pillow
Uso: python -m tools.quitar_fondo --input fotos --output fotos_sin_fondo --masks mascaras

Las imágenes RGB para COLMAP se guardan con fondo negro; las máscaras son
PNG de un canal y conservan exactamente el nombre del archivo RGB más .png.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


def process_folder(source: Path, output: Path, masks: Path, threshold: int = 128, transparent: Path | None = None) -> int:
    try:
        from rembg import new_session, remove
    except ImportError as exc:
        raise RuntimeError('Instalá dependencias: python -m pip install "rembg[cpu]" pillow') from exc
    if not 0 <= threshold <= 255:
        raise ValueError("threshold debe estar entre 0 y 255")
    source = Path(source).resolve()
    output = Path(output).resolve()
    masks = Path(masks).resolve()
    transparent = Path(transparent).resolve() if transparent is not None else None
    if transparent is not None and (transparent in (source, output, masks)
            or any(transparent.is_relative_to(p) or p.is_relative_to(transparent)
                   for p in (source, output, masks))):
        raise ValueError("La carpeta transparente debe ser independiente")
    if not source.is_dir():
        raise FileNotFoundError(source)
    if (output.is_relative_to(source) or masks.is_relative_to(source)
            or source.is_relative_to(output) or source.is_relative_to(masks)):
        raise ValueError("Las carpetas deben ser independientes, sin anidamiento")
    if source in (output, masks):
        raise ValueError("Las carpetas de salida deben diferir de la entrada")
    if output == masks:
        raise ValueError("Las carpetas de imágenes y máscaras deben ser distintas")
    files = sorted(p for p in source.iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONS)
    if not files:
        raise ValueError("No hay fotografías compatibles")
    if output.exists() or masks.exists() or (transparent is not None and transparent.exists()):
        raise FileExistsError("Las carpetas de salida deben ser nuevas")
    output.mkdir(parents=True, exist_ok=False)
    masks.mkdir(parents=True, exist_ok=False)
    if transparent is not None:
        transparent.mkdir(parents=True, exist_ok=False)
    session = new_session("u2net")
    for index, path in enumerate(files, 1):
        with Image.open(path) as image:
            rgba = remove(image.convert("RGB"), session=session)
            # rembg puede devolver PIL.Image o bytes, según versión/entrada.
            if not isinstance(rgba, Image.Image):
                from io import BytesIO
                rgba = Image.open(BytesIO(rgba))
            rgba = rgba.convert("RGBA")
            mask = rgba.getchannel("A").point(lambda value: 255 if value >= threshold else 0)
            # El RGB se compone sobre negro para evitar que COLMAP lea alfa.
            background = Image.new("RGBA", rgba.size, (0, 0, 0, 255))
            background.alpha_composite(rgba)
            name = f"{index:04d}.png"
            background.convert("RGB").save(output / name)
            mask.save(masks / (name + ".png"))
            if transparent is not None:
                rgba.putalpha(mask)
                rgba.save(transparent / name)
        print(f"Procesada {index}/{len(files)}: {path.name} -> {name}", flush=True)
    return len(files)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--masks", required=True, type=Path)
    parser.add_argument("--threshold", type=int, default=128)
    parser.add_argument("--transparent", type=Path, help="Salida opcional PNG con transparencia real")
    args = parser.parse_args()
    print(f"PROCESO TERMINADO: {process_folder(args.input, args.output, args.masks, args.threshold, args.transparent)} fotografías")


if __name__ == "__main__":
    main()
