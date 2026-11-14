#!/usr/bin/env python3
"""Auditoría topológica STL: componentes, bordes, orientación y advertencias de impresión."""
import argparse
from collections import Counter, defaultdict
import json
from verificar_stl import leer_stl
from medir_stl import medir


def auditar(caras, unidad='mm'):
    caras = list(caras)
    base = medir(caras, unidad)
    vertice_id = {}
    aristas = defaultdict(list)
    adyacencia = [set() for _ in caras]
    for i, tri in enumerate(caras):
        ids = [vertice_id.setdefault(tuple(p), len(vertice_id)) for p in tri]
        for a,b in ((ids[0],ids[1]),(ids[1],ids[2]),(ids[2],ids[0])):
            aristas[tuple(sorted((a,b)))].append((i,a,b))
    for incidencias in aristas.values():
        for i,_,_ in incidencias:
            adyacencia[i].update(j for j,_,_ in incidencias if j!=i)
    visitados=set(); tamanos=[]
    for inicio in range(len(caras)):
        if inicio in visitados: continue
        pila=[inicio]; visitados.add(inicio); n=0
        while pila:
            i=pila.pop(); n+=1
            for j in adyacencia[i]:
                if j not in visitados: visitados.add(j); pila.append(j)
        tamanos.append(n)
    bordes = [e for e,inc in aristas.items() if len(inc)==1]
    vertices_borde = Counter(v for edge in bordes for v in edge)
    # Un borde de superficie manifold forma lazos; las ramificaciones requieren inspección.
    ramificaciones = sum(n!=2 for n in vertices_borde.values())
    base.update({
        'vertices_unicos':len(vertice_id),
        'componentes_conectados':len(tamanos),
        'triangulos_por_componente':sorted(tamanos,reverse=True),
        'caracteristica_euler':len(vertice_id)-len(aristas)+len(caras),
        'vertices_de_borde_ramificados':ramificaciones,
        'apta_para_revision_de_impresion': base['volumen_estimado_valido_topologicamente'] and len(tamanos)==1,
        'nota': 'La auditoría no detecta autointersecciones, espesores insuficientes ni verifica la escala física.'
    })
    return base

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('archivo');p.add_argument('--unidad',choices=['mm','cm','m','in'],required=True)
    a=p.parse_args()
    print(json.dumps(auditar(leer_stl(a.archivo),a.unidad),indent=2,ensure_ascii=False))
