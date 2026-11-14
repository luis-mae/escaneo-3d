#!/usr/bin/env python3
"""Reducción experimental por agrupamiento de vértices en celdas 3D.
Puede alterar topología y dimensiones; no usar sin revisar la malla resultante.
"""
import argparse
import json
import math
from pathlib import Path
from verificar_stl import leer_stl, analizar
from reparar_stl import limpiar, escribir_binario


def reducir(caras, celda):
    if not math.isfinite(celda) or celda <= 0:
        raise ValueError('El tamaño de celda debe ser positivo y finito')
    caras = list(caras)
    grupos = {}
    for tri in caras:
        for p in tri:
            if not all(math.isfinite(x) for x in p):
                raise ValueError('Coordenadas no finitas')
            key = tuple(math.floor(x / celda) for x in p)
            if key not in grupos:
                grupos[key] = [0.0, 0.0, 0.0, 0]
            g = grupos[key]
            for i in range(3):
                g[i] += p[i]
            g[3] += 1
    centroides = {key: tuple(g[i] / g[3] for i in range(3)) for key, g in grupos.items()}
    nuevas = [tuple(centroides[tuple(math.floor(x / celda) for x in p)] for p in tri) for tri in caras]
    salida, limpieza = limpiar(nuevas, tolerancia=1e-12)
    return salida, {'triangulos_originales': len(caras), 'triangulos_finales': len(salida),
                    'vertices_agrupados': len(centroides), 'tamano_celda': celda,
                    'limpieza': limpieza, 'advertencia': 'La reducción puede abrir huecos, alterar detalles y afectar la precisión. Revisar topología y escala.'}


def ejecutar(entrada, salida, celda):
    if Path(entrada).resolve() == Path(salida).resolve():
        raise ValueError('No se permite sobrescribir el original')
    caras, datos = reducir(leer_stl(entrada), celda)
    if not caras:
        raise ValueError('La reducción eliminó toda la geometría; reducir tamaño de celda')
    escribir_binario(salida, caras)
    return {**datos, 'diagnostico': analizar(salida)}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('entrada'); p.add_argument('salida')
    p.add_argument('--celda', type=float, required=True, help='Tamaño en unidades del STL')
    a = p.parse_args()
    print(json.dumps(ejecutar(a.entrada, a.salida, a.celda), ensure_ascii=False, indent=2))
