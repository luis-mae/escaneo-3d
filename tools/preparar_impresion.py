#!/usr/bin/env python3
"""Pipeline local conservador: diagnostica, limpia y orienta una malla STL.

Nunca reemplaza el original; emite informe JSON con advertencias de impresión.
"""
import argparse
import json
from pathlib import Path
from verificar_stl import leer_stl
from reparar_stl import limpiar, escribir_binario
from orientar_stl import orientar
from auditar_malla import auditar


def preparar(entrada, salida, unidad='mm', corregir_orientacion=False):
    entrada, salida = Path(entrada), Path(salida)
    if entrada.resolve() == salida.resolve():
        raise ValueError('No se permite sobrescribir el archivo original')
    if unidad not in ('mm', 'cm', 'm', 'in'):
        raise ValueError('Unidad no válida')
    caras = list(leer_stl(entrada))
    if not caras:
        raise ValueError('STL sin triángulos')
    antes = auditar(caras, unidad)
    limpias, cambios = limpiar(caras)
    if not limpias:
        raise ValueError('La limpieza eliminó todos los triángulos')
    info_orientacion = None
    if corregir_orientacion:
        limpias, info_orientacion = orientar(limpias)
    despues = auditar(limpias, unidad)
    salida.parent.mkdir(parents=True, exist_ok=True)
    escribir_binario(salida, limpias)
    advertencias = []
    if despues['aristas_abiertas']:
        advertencias.append('La malla tiene bordes abiertos; puede no ser imprimible')
    if despues['aristas_no_manifold']:
        advertencias.append('La malla contiene aristas no manifold')
    if despues['componentes_conectados'] != 1:
        advertencias.append('La malla contiene múltiples componentes')
    advertencias.append('La escala y las tolerancias físicas deben verificarse antes de fabricar')
    return {'entrada': str(entrada), 'salida': str(salida), 'unidad_declarada': unidad,
            'antes': antes, 'despues': despues, 'limpieza': cambios,
            'orientacion': info_orientacion, 'advertencias': advertencias,
            'apta_para_revision': despues['apta_para_revision_de_impresion'],
            'nota': 'No certifica imprimibilidad, precisión dimensional ni ausencia de autointersecciones.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('entrada'); p.add_argument('salida')
    p.add_argument('--unidad', required=True, choices=['mm', 'cm', 'm', 'in'])
    p.add_argument('--orientar', action='store_true')
    p.add_argument('--informe', help='Ruta opcional para guardar el informe JSON')
    a = p.parse_args()
    resultado = preparar(a.entrada, a.salida, a.unidad, a.orientar)
    reporte = json.dumps(resultado, ensure_ascii=False, indent=2)
    if a.informe:
        Path(a.informe).write_text(reporte, encoding='utf-8')
    print(reporte)
