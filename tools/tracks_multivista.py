"""Construye trayectorias de puntos observados en varias imágenes.

Entrada: correspondencias (imagen_a, indice_a, imagen_b, indice_b).
Rechaza fusiones que asignarían dos puntos distintos a una misma imagen.
No estima cámaras ni reconstruye por sí solo geometría 3D.
"""
from collections import defaultdict


def construir_tracks(correspondencias, minimo_vistas=2):
    if minimo_vistas < 2:
        raise ValueError('minimo_vistas debe ser >= 2')
    parent = {}
    views = {}
    rechazadas = 0

    def find(x):
        parent.setdefault(x, x)
        views.setdefault(x, {x[0]: x[1]})
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    for ia, pa, ib, pb in correspondencias:
        if ia == ib:
            rechazadas += 1
            continue
        a, b = (ia, pa), (ib, pb)
        ra, rb = find(a), find(b)
        if ra == rb:
            continue
        if any(k in views[ra] and views[ra][k] != v for k, v in views[rb].items()):
            rechazadas += 1
            continue
        if len(views[ra]) < len(views[rb]):
            ra, rb = rb, ra
        parent[rb] = ra
        views[ra].update(views[rb])
        del views[rb]

    tracks = [dict(sorted(v.items(), key=lambda p: str(p[0]))) for v in views.values()
              if len(v) >= minimo_vistas]
    tracks.sort(key=lambda t: (-len(t), str(list(t.items()))))
    return {'tracks': tracks, 'total_tracks': len(tracks), 'correspondencias_rechazadas': rechazadas}
