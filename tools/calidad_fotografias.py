"""Evaluación local de fotografías: exposición, detalle y duplicados aproximados.

Herramienta auxiliar; NO certifica que una imagen sirva para fotogrametría.
Dependencia: Pillow. Los originales nunca se modifican.
"""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageOps, ImageStat, UnidentifiedImageError

EXTENSIONES = {'.jpg', '.jpeg', '.png', '.webp', '.heic'}


def analizar_imagen(ruta: Path):
    try:
        with Image.open(ruta) as original:
            im = ImageOps.exif_transpose(original).convert('L')
            ancho, alto = im.size
            mini = im.resize((64, 64))
            valores = list(mini.getdata())
            promedio = sum(valores) / len(valores)
            negros = sum(x < 18 for x in valores) / len(valores)
            blancos = sum(x > 237 for x in valores) / len(valores)
            # Promedio de diferencias entre píxeles vecinos: proxy de detalle,
            # no estimación física de desenfoque ni de calidad geométrica.
            detalle = sum(abs(valores[y*64+x] - valores[y*64+x-1]) for y in range(64) for x in range(1, 64)) / (64*63)
            huella = tuple(im.resize((8, 8)).getdata())
            problemas = []
            if min(ancho, alto) < 720:
                problemas.append('resolucion_baja')
            if promedio < 45 or negros > .65:
                problemas.append('subexposicion')
            if promedio > 215 or blancos > .65:
                problemas.append('sobreexposicion')
            if detalle < 3:
                problemas.append('poco_detalle_o_desenfoque')
            return {'archivo': ruta.name, 'dimensiones': [ancho, alto], 'brillo': round(promedio, 1),
                    'detalle_aproximado': round(detalle, 2), 'problemas': problemas,
                    'estado': 'revisar' if problemas else 'apta_preliminar', '_huella': huella}
    except (OSError, ValueError, UnidentifiedImageError) as exc:
        return {'archivo': ruta.name, 'estado': 'no_decodificable', 'problemas': ['archivo_invalido'], 'error': str(exc)}


def analizar_carpeta(carpeta: Path):
    if not carpeta.is_dir():
        raise NotADirectoryError(carpeta)
    resultados = [analizar_imagen(p) for p in sorted(carpeta.iterdir())
                  if p.is_file() and p.suffix.lower() in EXTENSIONES]
    anteriores = []
    for r in resultados:
        huella = r.pop('_huella', None)
        if huella is not None:
            for nombre, previa in anteriores:
                diferencia = sum(abs(a-b) for a,b in zip(huella, previa)) / len(huella)
                if diferencia < 1.5:
                    r['problemas'].append('posible_duplicado_de_' + nombre)
                    r['estado'] = 'revisar'
                    break
            anteriores.append((r['archivo'], huella))
    return {'cantidad': len(resultados), 'imagenes': resultados,
            'advertencia': 'Evaluación heurística: revisar visualmente; no mide precisión 3D ni garantiza reconstrucción.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('carpeta', type=Path)
    args = parser.parse_args()
    print(json.dumps(analizar_carpeta(args.carpeta), indent=2, ensure_ascii=False))
