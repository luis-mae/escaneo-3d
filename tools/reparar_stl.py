#!/usr/bin/env python3
"""Limpieza conservadora STL: elimina triángulos degenerados y duplicados.
No cierra agujeros ni asegura imprimibilidad. Conserva unidades originales.
"""
import argparse
import json
import math
import struct
from pathlib import Path
from verificar_stl import leer_stl, analizar


def limpiar(caras, tolerancia=1e-10):
    vistas = set()
    resultado = []
    estadisticas = {'degenerados_eliminados': 0, 'duplicados_eliminados': 0}
    for cara in caras:
        if any(not math.isfinite(x) for p in cara for x in p):
            raise ValueError('La malla contiene coordenadas no finitas')
        a, b, c = cara
        u = [b[i]-a[i] for i in range(3)]
        v = [c[i]-a[i] for i in range(3)]
        cr = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
        if sum(x*x for x in cr) <= tolerancia*tolerancia:
            estadisticas['degenerados_eliminados'] += 1
            continue
        clave = tuple(sorted(cara))
        if clave in vistas:
            estadisticas['duplicados_eliminados'] += 1
            continue
        vistas.add(clave)
        resultado.append(cara)
    return resultado, estadisticas


def escribir_binario(ruta, caras):
    ruta = Path(ruta)
    if len(caras) > 0xffffffff:
        raise ValueError('Demasiados triángulos para STL')
    with ruta.open('wb') as f:
        f.write(b'Escaneo3D - limpieza conservadora'.ljust(80, b' '))
        f.write(struct.pack('<I', len(caras)))
        for a, b, c in caras:
            u = [b[i]-a[i] for i in range(3)]
            v = [c[i]-a[i] for i in range(3)]
            n = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
            norma = math.sqrt(sum(x*x for x in n))
            normal = [x/norma for x in n] if norma else [0.0, 0.0, 0.0]
            f.write(struct.pack('<12fH', *(normal + list(a) + list(b) + list(c)), 0))


def reparar(entrada, salida):
    if Path(entrada).resolve() == Path(salida).resolve():
        raise ValueError('La salida debe ser distinta del archivo original')
    caras, cambios = limpiar(leer_stl(entrada))
    if not caras:
        raise ValueError('No quedan triángulos válidos')
    escribir_binario(salida, caras)
    return {'salida': str(salida), **cambios, 'diagnostico': analizar(salida),
            'nota': 'No se reparan agujeros ni aristas no manifold; validar antes de imprimir.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('entrada')
    parser.add_argument('salida')
    args = parser.parse_args()
    print(json.dumps(reparar(args.entrada, args.salida), ensure_ascii=False, indent=2))
