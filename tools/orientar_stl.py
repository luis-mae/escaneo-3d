#!/usr/bin/env python3
"""Orienta triángulos STL por conectividad y, en sólidos cerrados, hacia afuera.
No repara geometría ni garantiza imprimibilidad. Conserva el original.
"""
import argparse
from collections import defaultdict, deque
import json
from pathlib import Path
from verificar_stl import leer_stl, analizar
from reparar_stl import escribir_binario


def orientar(caras):
    caras = [tuple(tuple(p) for p in t) for t in caras]
    edges = defaultdict(list)
    for i, tri in enumerate(caras):
        if len(set(tri)) != 3:
            raise ValueError('Hay triángulos degenerados; limpiar antes de orientar')
        for a,b in ((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])):
            key=tuple(sorted((a,b)))
            edges[key].append((i, 1 if (a,b)==key else -1))
    adjacency=defaultdict(list)
    for entries in edges.values():
        if len(entries)==2:
            (a,sa),(b,sb)=entries
            adjacency[a].append((b,sa==sb))
            adjacency[b].append((a,sa==sb))
    flips={}; components=[]; conflicts=0
    for start in range(len(caras)):
        if start in flips: continue
        flips[start]=False; comp=[]; q=deque([start]); inconsistent=False
        while q:
            i=q.popleft();comp.append(i)
            for j, same in adjacency[i]:
                expected=flips[i]^same
                if j in flips:
                    if flips[j]!=expected:
                        inconsistent=True; conflicts+=1
                else:
                    flips[j]=expected;q.append(j)
        components.append((comp,inconsistent))
    result=[(tri[0],tri[2],tri[1]) if flips[i] else tri for i,tri in enumerate(caras)]
    outward=0; skipped=0
    for comp,inconsistent in components:
        comp_set=set(comp)
        closed=not inconsistent and all(len(entries)==2 for entries in edges.values() if any(i in comp_set for i,_ in entries))
        if not closed:
            skipped+=1;continue
        volume6=0.0
        for i in comp:
            a,b,c=result[i]
            volume6 += a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0])
        if volume6 < 0:
            for i in comp:
                a,b,c=result[i];result[i]=(a,c,b)
            outward+=1
    return result, {'componentes':len(components),'caras_invertidas_por_coherencia':sum(flips.values()),
                    'componentes_invertidos_hacia_afuera':outward,'componentes_no_cerrados_o_conflictivos':skipped,
                    'conflictos_orientacion':conflicts,'aristas_no_manifold':sum(len(v)>2 for v in edges.values())}


def ejecutar(entrada,salida):
    if Path(entrada).resolve()==Path(salida).resolve(): raise ValueError('No sobrescribir el original')
    caras,stats=orientar(leer_stl(entrada))
    escribir_binario(salida,caras)
    return {**stats,'diagnostico':analizar(salida),'advertencia':'Orientación no equivale a reparación ni certificación de imprimibilidad.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('entrada');p.add_argument('salida');a=p.parse_args()
    print(json.dumps(ejecutar(a.entrada,a.salida),ensure_ascii=False,indent=2))
