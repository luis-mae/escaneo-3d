#!/usr/bin/env python3
"""Optimización STL por soldadura de vértices próximos (tolerancia en unidades del archivo).
No es decimación ni garantiza una malla imprimible. Nunca altera el original.
"""
import argparse
import json
import math
from pathlib import Path
from reparar_stl import limpiar, escribir_binario
from verificar_stl import leer_stl, analizar


def optimizar(caras, tolerancia=0.001):
    if not math.isfinite(tolerancia) or tolerancia <= 0:
        raise ValueError('La tolerancia debe ser positiva y finita')
    # Grid hash + 27 neighboring cells avoids merging only on grid boundaries.
    buckets = {}
    canonical = []
    def weld(p):
        if not all(math.isfinite(x) for x in p):
            raise ValueError('Coordenadas no finitas')
        cell = tuple(math.floor(x/tolerancia) for x in p)
        best = None
        best_dist = tolerancia*tolerancia
        for i in (-1,0,1):
            for j in (-1,0,1):
                for k in (-1,0,1):
                    for idx in buckets.get((cell[0]+i,cell[1]+j,cell[2]+k),[]):
                        q=canonical[idx]
                        d=sum((p[t]-q[t])**2 for t in range(3))
                        if d < best_dist:
                            best_dist=d; best=idx
        if best is not None:
            return canonical[best]
        idx=len(canonical);canonical.append(tuple(p));buckets.setdefault(cell,[]).append(idx)
        return canonical[idx]
    input_vertices=set(tuple(p) for tri in caras for p in tri)
    welded=[tuple(weld(p) for p in tri) for tri in caras]
    # Area threshold proportional to tolerance; collapsed triangles are removed.
    clean, stats=limpiar(welded,tolerancia=max(1e-12,tolerancia*tolerancia*0.01))
    return clean, {'triangulos_originales':len(caras),'triangulos_finales':len(clean),
                   'vertices_originales':len(input_vertices),'vertices_finales':len(set(p for tri in clean for p in tri)),
                   'tolerancia':tolerancia,**stats}


def ejecutar(entrada,salida,tolerancia=0.001):
    if Path(entrada).resolve()==Path(salida).resolve():
        raise ValueError('La salida debe ser distinta del original')
    caras, stats=optimizar(leer_stl(entrada),tolerancia)
    if not caras: raise ValueError('La tolerancia eliminó toda la geometría')
    escribir_binario(salida,caras)
    return {**stats,'diagnostico':analizar(salida),
            'advertencia':'La soldadura modifica coordenadas dentro de la tolerancia; no equivale a decimación ni garantiza imprimibilidad.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('entrada');p.add_argument('salida');p.add_argument('--tolerancia',type=float,default=0.001)
    a=p.parse_args()
    print(json.dumps(ejecutar(a.entrada,a.salida,a.tolerancia),ensure_ascii=False,indent=2))
