#!/usr/bin/env python3
"""Simplificación conservadora de STL por agrupamiento espacial de vértices.

No garantiza preservar detalles finos ni topología: inspeccionar el resultado.
"""
import argparse
import json
import math
from pathlib import Path
from verificar_stl import leer_stl
from reparar_stl import escribir_binario
from auditar_malla import auditar


def optimizar(caras, celda):
    if not math.isfinite(celda) or celda <= 0:
        raise ValueError('La celda debe ser positiva y finita')
    caras = list(caras)
    grupos = {}
    for cara in caras:
        for v in cara:
            if len(v) != 3 or not all(math.isfinite(float(x)) for x in v):
                raise ValueError('Vértice inválido')
            key = tuple(math.floor(float(x) / celda) for x in v)
            if key not in grupos:
                grupos[key] = [0.0, 0.0, 0.0, 0]
            g = grupos[key]
            for i in range(3):
                g[i] += float(v[i])
            g[3] += 1
    centros = {k: tuple(g[i] / g[3] for i in range(3)) for k, g in grupos.items()}
    salida = []
    vistos = set()
    for cara in caras:
        puntos = [centros[tuple(math.floor(float(x) / celda) for x in v)] for v in cara]
        if len(set(puntos)) < 3:
            continue
        a, b, c = puntos
        ab = [b[i] - a[i] for i in range(3)]
        ac = [c[i] - a[i] for i in range(3)]
        cross = (ab[1]*ac[2]-ab[2]*ac[1], ab[2]*ac[0]-ab[0]*ac[2], ab[0]*ac[1]-ab[1]*ac[0])
        if sum(x*x for x in cross) <= 1e-24:
            continue
        clave = tuple(sorted(puntos))
        if clave not in vistos:
            vistos.add(clave)
            salida.append(tuple(puntos))
    return salida


def procesar(entrada, salida, celda, unidad='mm'):
    entrada, salida = Path(entrada), Path(salida)
    if entrada.resolve() == salida.resolve():
        raise ValueError('No se permite sobrescribir el original')
    caras = list(leer_stl(entrada))
    if not caras:
        raise ValueError('STL vacío')
    reducidas = optimizar(caras, celda)
    if not reducidas:
        raise ValueError('La resolución elegida elimina toda la geometría; usar celda menor')
    salida.parent.mkdir(parents=True, exist_ok=True)
    escribir_binario(salida, reducidas)
    return {'triangulos_antes': len(caras), 'triangulos_despues': len(reducidas),
            'reduccion_porcentual': round(100 * (1-len(reducidas)/len(caras)), 2),
            'celda': celda, 'unidad': unidad, 'auditoria': auditar(reducidas, unidad),
            'advertencia': 'Simplificación experimental: comprobar escala, topología y detalle antes de imprimir.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('entrada'); p.add_argument('salida')
    p.add_argument('--celda', type=float, required=True, help='Tamaño de agrupamiento en la unidad del STL')
    p.add_argument('--unidad', choices=['mm', 'cm', 'm', 'in'], default='mm')
    p.add_argument('--informe')
    a = p.parse_args()
    resultado = procesar(a.entrada, a.salida, a.celda, a.unidad)
    texto = json.dumps(resultado, indent=2, ensure_ascii=False)
    if a.informe:
        Path(a.informe).write_text(texto, encoding='utf-8')
    print(texto)
