#!/usr/bin/env python3
"""Reparación conservadora y verificable de STL; nunca sobrescribe la entrada.

Cierra únicamente contornos pequeños, planos y convexos con el algoritmo
experimental existente. No certifica que una pieza sea imprimible.
"""
import argparse
import json
import os
import tempfile
from pathlib import Path
from verificar_stl import leer_stl, analizar
from reparar_stl import limpiar, escribir_binario
from cerrar_agujeros import cerrar


def reparar_controlado(entrada, salida, cerrar_pequenos=False, max_vertices=12):
    origen, destino = Path(entrada), Path(salida)
    if origen.resolve() == destino.resolve():
        raise ValueError('No se permite sobrescribir el STL original')
    if not 3 <= max_vertices <= 64:
        raise ValueError('max_vertices debe estar entre 3 y 64')
    antes = analizar(origen)
    caras, limpieza = limpiar(leer_stl(origen))
    if not caras:
        raise ValueError('La limpieza dejó una malla vacía')
    cierre = {'agujeros_cerrados': 0, 'agujeros_omitidos': 0, 'triangulos_agregados': 0}
    if cerrar_pequenos:
        caras, datos = cerrar(caras, max_vertices=max_vertices)
        cierre = {k: datos[k] for k in cierre}
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = None
    try:
        with tempfile.NamedTemporaryFile(prefix='.escaneo-', suffix='.stl', dir=destino.parent, delete=False) as f:
            temporal = Path(f.name)
        escribir_binario(temporal, caras)
        despues = analizar(temporal)
        # A repair must never introduce non-manifold edges or degenerate faces.
        if (despues['aristas_no_manifold'] > antes['aristas_no_manifold'] or
                despues['triangulos_degenerados'] > antes['triangulos_degenerados']):
            raise ValueError('La reparación empeoró la topología; no se guardó')
        if destino.exists():
            raise FileExistsError('La salida ya existe; elegí otro nombre para conservar versiones')
        os.replace(temporal, destino)
        temporal = None
    finally:
        if temporal is not None:
            temporal.unlink(missing_ok=True)
    return {
        'entrada': str(origen), 'salida': str(destino),
        'antes': antes, 'despues': {**despues, 'archivo': str(destino)},
        'limpieza': limpieza, 'cierre': cierre,
        'lista_para_revision': despues['malla_cerrada_por_aristas'],
        'advertencia': 'No comprueba autointersecciones, espesores, escala ni tolerancias dimensionales. Revisar visualmente antes de imprimir.'
    }


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('entrada'); p.add_argument('salida')
    p.add_argument('--cerrar-pequenos', action='store_true')
    p.add_argument('--max-vertices', type=int, default=12)
    a = p.parse_args()
    print(json.dumps(reparar_controlado(a.entrada, a.salida, a.cerrar_pequenos, a.max_vertices), ensure_ascii=False, indent=2))
