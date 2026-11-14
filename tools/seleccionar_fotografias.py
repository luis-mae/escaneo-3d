"""Preselección conservadora de fotografías para un procesamiento posterior.

No estima posiciones de cámara ni asegura cobertura angular o reconstrucción.
"""
import argparse
import json
from pathlib import Path
from tools.calidad_fotografias import analizar_carpeta


def seleccionar(carpeta: Path, maximo: int = 60):
    if maximo < 1:
        raise ValueError('maximo debe ser positivo')
    informe = analizar_carpeta(carpeta)
    elegidas, descartadas = [], []
    for imagen in informe['imagenes']:
        problemas = imagen['problemas']
        motivo = None
        if imagen['estado'] == 'no_decodificable':
            motivo = 'archivo_invalido'
        elif any(p.startswith('posible_duplicado_de_') for p in problemas):
            motivo = 'posible_duplicado'
        elif 'subexposicion' in problemas or 'sobreexposicion' in problemas:
            motivo = 'exposicion_deficiente'
        elif 'resolucion_baja' in problemas:
            motivo = 'resolucion_baja'
        elif 'poco_detalle_o_desenfoque' in problemas:
            motivo = 'detalle_insuficiente'
        elif len(elegidas) >= maximo:
            motivo = 'limite_de_imagenes'
        if motivo:
            descartadas.append({'archivo': imagen['archivo'], 'motivo': motivo})
        else:
            elegidas.append(imagen['archivo'])
    return {'seleccionadas': elegidas, 'descartadas': descartadas,
            'cantidad_seleccionadas': len(elegidas),
            'advertencia': 'Selección heurística. No verifica diversidad angular, enfoque real ni calidad de reconstrucción.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('carpeta', type=Path)
    p.add_argument('--maximo', type=int, default=60)
    args = p.parse_args()
    print(json.dumps(seleccionar(args.carpeta, args.maximo), ensure_ascii=False, indent=2))
