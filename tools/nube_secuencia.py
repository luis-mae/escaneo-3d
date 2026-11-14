"""Reconstrucción dispersa por pares consecutivos, sin fusionar escalas incompatibles.

Cada par tiene su propio marco y escala arbitraria. No es una malla imprimible.
"""
import argparse
import json
from pathlib import Path
from tools.nube_dos_vistas import reconstruir_par, guardar_ply


def procesar_secuencia(fotos, focal_px, salida, min_puntos=12):
    fotos = [Path(p) for p in fotos]
    if len(fotos) < 2:
        raise ValueError('Se necesitan al menos dos fotografías')
    if min_puntos < 8:
        raise ValueError('min_puntos debe ser >= 8')
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    informe = {'tipo': 'nubes_dispersas_por_pares', 'escala': 'arbitraria_por_par',
               'fusionadas': False, 'pares': [],
               'advertencia': 'Las nubes no comparten escala ni sistema de coordenadas. No son una malla imprimible.'}
    for i, (a, b) in enumerate(zip(fotos, fotos[1:])):
        resultado = reconstruir_par(a, b, focal_px, min_puntos=min_puntos)
        registro = {'indice': i, 'foto_a': a.name, 'foto_b': b.name,
                    'estado': resultado['estado'], 'aceptados': resultado.get('aceptados', 0)}
        if resultado['estado'] == 'experimental' and resultado.get('aceptados', 0):
            nombre = f'par_{i:03d}.ply'
            guardar_ply(resultado['puntos'], salida / nombre)
            registro['archivo'] = nombre
        else:
            registro['motivo'] = resultado.get('motivo', 'Sin puntos triangulables')
        informe['pares'].append(registro)
    (salida / 'informe.json').write_text(json.dumps(informe, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return informe


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('fotos', nargs='+', type=Path)
    p.add_argument('--focal-px', type=float, required=True)
    p.add_argument('--salida', type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(procesar_secuencia(args.fotos, args.focal_px, args.salida), ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
