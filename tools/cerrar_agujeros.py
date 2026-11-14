#!/usr/bin/env python3
"""Cierre experimental de agujeros pequeños, planos y convexos en mallas STL.
No es un reparador universal: rechaza contornos ambiguos, no planos o cóncavos.
"""
import argparse
import json
import math
from pathlib import Path
from reparar_stl import escribir_binario, limpiar
from verificar_stl import leer_stl, analizar


def cerrar(caras, max_vertices=12, tolerancia_plano=1e-5):
    caras, limpieza = limpiar(caras)
    aristas = {}
    for tri in caras:
        for a,b in ((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])):
            key = tuple(sorted((a,b)))
            aristas.setdefault(key, []).append((a,b))
    frontera = [oriented[0] for oriented in aristas.values() if len(oriented)==1]
    salida = dict(limpieza, agujeros_cerrados=0, agujeros_omitidos=0, triangulos_agregados=0)
    # A vertex in a simple boundary must have exactly one incoming and one outgoing edge.
    outgoing, incoming = {}, {}
    for a,b in frontera:
        outgoing.setdefault(a, []).append(b)
        incoming.setdefault(b, []).append(a)
    visited = set()
    for start in list(outgoing):
        if start in visited:
            continue
        loop=[]; current=start
        while current not in visited and len(loop)<=max_vertices:
            visited.add(current); loop.append(current)
            if len(outgoing.get(current,[]))!=1 or len(incoming.get(current,[]))!=1:
                break
            current=outgoing[current][0]
        if current!=start or not (3<=len(loop)<=max_vertices):
            salida['agujeros_omitidos']+=1
            continue
        # Newell normal and planar projection.
        nx=ny=nz=0.
        for a,b in zip(loop,loop[1:]+loop[:1]):
            nx+=(a[1]-b[1])*(a[2]+b[2]); ny+=(a[2]-b[2])*(a[0]+b[0]); nz+=(a[0]-b[0])*(a[1]+b[1])
        length=math.sqrt(nx*nx+ny*ny+nz*nz)
        if length<1e-12:
            salida['agujeros_omitidos']+=1; continue
        n=(nx/length,ny/length,nz/length)
        center=tuple(sum(p[i] for p in loop)/len(loop) for i in range(3))
        extent=max(math.dist(a,b) for a in loop for b in loop)
        if any(abs(sum((p[i]-center[i])*n[i] for i in range(3)))>tolerancia_plano*max(extent,1e-12) for p in loop):
            salida['agujeros_omitidos']+=1; continue
        axis=max(range(3),key=lambda i:abs(n[i]))
        xy=[tuple(p[i] for i in range(3) if i!=axis) for p in loop]
        cross=[]
        for i in range(len(xy)):
            a,b,c=xy[i-1],xy[i],xy[(i+1)%len(xy)]
            cross.append((b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0]))
        if not (all(v>1e-12 for v in cross) or all(v< -1e-12 for v in cross)):
            salida['agujeros_omitidos']+=1; continue
        # Reverse boundary orientation to oppose existing faces.
        for a,b in zip(loop,loop[1:]+loop[:1]):
            caras.append((b,a,center))
            salida['triangulos_agregados']+=1
        salida['agujeros_cerrados']+=1
    return caras,salida


def ejecutar(entrada,salida,max_vertices=12):
    if Path(entrada).resolve()==Path(salida).resolve():
        raise ValueError('La salida debe ser distinta del original')
    caras,stats=cerrar(leer_stl(entrada),max_vertices=max_vertices)
    escribir_binario(salida,caras)
    return {**stats,'diagnostico':analizar(salida),'advertencia':'Reparación experimental. Verificar escala, geometría y estanqueidad antes de imprimir.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('entrada');p.add_argument('salida');p.add_argument('--max-vertices',type=int,default=12)
    a=p.parse_args();print(json.dumps(ejecutar(a.entrada,a.salida,a.max_vertices),ensure_ascii=False,indent=2))
