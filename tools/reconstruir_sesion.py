"""Procesa pares consecutivos de una sesión y exporta nubes PLY separadas.

IMPORTANTE: cada par usa un marco y escala arbitrarios independientes; NO se
fusionan ni constituyen un único objeto 3D. No es apto para fabricación.
"""
import argparse
import hashlib
import json
from pathlib import Path
from tools.nube_dos_vistas import reconstruir_par, guardar_ply


def ejecutar(manifiesto: Path, carpeta: Path, salida: Path, focal_px: float, procesador=reconstruir_par):
    if focal_px <= 0:
        raise ValueError('focal_px debe ser positivo')
    data = json.loads(Path(manifiesto).read_text(encoding='utf-8'))
    fotos = data.get('imagenes', [])
    if len(fotos) < 2:
        raise ValueError('Se necesitan al menos dos imágenes')
    carpeta = Path(carpeta).resolve()
    salida = Path(salida).resolve()
    if salida == carpeta or carpeta in salida.parents:
        raise ValueError('La salida debe estar fuera de la carpeta de fotografías')
    rutas = []
    for item in fotos:
        nombre = item['archivo']
        ruta = (carpeta / nombre).resolve()
        if ruta.parent != carpeta or not ruta.is_file():
            raise ValueError('Imagen ausente o ruta insegura: ' + nombre)
        if hashlib.sha256(ruta.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('La imagen cambió desde el manifiesto: ' + nombre)
        rutas.append(ruta)
    salida.mkdir(parents=True, exist_ok=True)
    pares = []
    for i, (a, b) in enumerate(zip(rutas, rutas[1:]), 1):
        try:
            resultado = procesador(a, b, focal_px)
            registro = {'indice': i, 'foto_a': a.name, 'foto_b': b.name,
                        'estado': resultado['estado'], 'puntos': resultado.get('aceptados', 0)}
            if resultado['estado'] == 'experimental' and resultado.get('aceptados', 0):
                nombre = f'par_{i:03d}.ply'
                guardar_ply(resultado['puntos'], salida / nombre)
                registro['archivo_ply'] = nombre
            else:
                registro['motivo'] = resultado.get('motivo', 'sin puntos aceptados')
        except (ValueError, RuntimeError) as exc:
            registro = {'indice': i, 'foto_a': a.name, 'foto_b': b.name,
                        'estado': 'error', 'motivo': str(exc)}
        pares.append(registro)
    informe = {'estado': 'experimental', 'pares': pares,
               'pares_con_nube': sum('archivo_ply' in p for p in pares),
               'escala': 'arbitraria e independiente por par',
               'advertencia': 'NO fusionar estas nubes directamente: faltan poses globales, escala común y ajuste multivista.'}
    (salida / 'informe.json').write_text(json.dumps(informe, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return informe


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifiesto', type=Path)
    p.add_argument('carpeta_fotos', type=Path)
    p.add_argument('--salida', type=Path, required=True)
    p.add_argument('--focal-px', type=float, required=True)
    a = p.parse_args()
    result = ejecutar(a.manifiesto, a.carpeta_fotos, a.salida, a.focal_px)
    print(json.dumps({k: v for k, v in result.items() if k != 'pares'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
