#!/usr/bin/env python3
"""Compara malla original y optimizada; alerta cambios de escala y topología."""
import argparse
import json
from verificar_stl import leer_stl
from auditar_malla import auditar


def comparar(original, resultado, unidad='mm', tolerancia_pct=1.0):
    if tolerancia_pct < 0:
        raise ValueError('La tolerancia debe ser no negativa')
    antes = auditar(original, unidad)
    despues = auditar(resultado, unidad)
    cambios = []
    for x, y in zip(antes['dimensiones_mm'], despues['dimensiones_mm']):
        cambios.append(round(100 * abs(y-x) / x, 5) if x else (0.0 if y == 0 else None))
    alertas = []
    if any(v is None or v > tolerancia_pct for v in cambios):
        alertas.append('Cambio dimensional superior a la tolerancia')
    if despues['aristas_abiertas'] > antes['aristas_abiertas']:
        alertas.append('Aumentaron las aristas abiertas')
    if despues['aristas_no_manifold'] > antes['aristas_no_manifold']:
        alertas.append('Aumentaron las aristas no manifold')
    if despues['componentes_conectados'] != antes['componentes_conectados']:
        alertas.append('Cambió la cantidad de componentes')
    return {'triangulos_antes': antes['triangulos'], 'triangulos_despues': despues['triangulos'],
            'reduccion_pct': round(100*(1-despues['triangulos']/antes['triangulos']), 3),
            'variacion_dimensional_pct': cambios, 'tolerancia_pct': tolerancia_pct,
            'alertas': alertas, 'revision_recomendada': bool(alertas),
            'nota': 'La comparación no garantiza fidelidad de superficies ni detecta autointersecciones.'}


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('original'); p.add_argument('resultado')
    p.add_argument('--unidad', choices=['mm','cm','m','in'], required=True)
    p.add_argument('--tolerancia-pct', type=float, default=1.0)
    a=p.parse_args()
    print(json.dumps(comparar(leer_stl(a.original), leer_stl(a.resultado), a.unidad, a.tolerancia_pct), ensure_ascii=False, indent=2))
