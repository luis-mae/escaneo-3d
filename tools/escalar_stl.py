#!/usr/bin/env python3
"""Escala una malla STL usando una dimensión física conocida (sin alterar el original)."""
import argparse
import json
import math
from pathlib import Path
from verificar_stl import leer_stl
from reparar_stl import escribir_binario


def escalar(entrada, salida, eje, medida_mm):
    entrada, salida = Path(entrada), Path(salida)
    if entrada.resolve() == salida.resolve():
        raise ValueError('No se permite sobrescribir el original')
    if eje not in ('x', 'y', 'z'):
        raise ValueError('Eje inválido')
    if not math.isfinite(medida_mm) or medida_mm <= 0:
        raise ValueError('La medida física debe ser positiva y finita')
    caras = list(leer_stl(entrada))
    if not caras:
        raise ValueError('STL vacío')
    idx = {'x': 0, 'y': 1, 'z': 2}[eje]
    valores = [v[idx] for cara in caras for v in cara]
    amplitud = max(valores) - min(valores)
    if amplitud <= 1e-12:
        raise ValueError('La dimensión elegida es nula')
    factor = medida_mm / amplitud
    if not math.isfinite(factor):
        raise ValueError('Factor de escala inválido')
    nuevas = [tuple(tuple(coord * factor for coord in v) for v in cara) for cara in caras]
    salida.parent.mkdir(parents=True, exist_ok=True)
    escribir_binario(salida, nuevas)
    return {'entrada': str(entrada), 'salida': str(salida), 'eje_referencia': eje,
            'dimension_modelo_original': amplitud, 'dimension_real_mm': medida_mm,
            'factor': factor, 'advertencia': 'La exactitud depende de la medida aportada y de la geometría reconstruida.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('entrada'); p.add_argument('salida')
    p.add_argument('--eje', choices=['x', 'y', 'z'], required=True)
    p.add_argument('--medida-mm', type=float, required=True)
    a = p.parse_args()
    print(json.dumps(escalar(a.entrada, a.salida, a.eje, a.medida_mm), ensure_ascii=False, indent=2))
