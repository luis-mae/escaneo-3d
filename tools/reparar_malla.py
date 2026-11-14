"""Reparación conservadora de mallas triangulares OBJ.

Elimina caras degeneradas/duplicadas, orienta caras vecinas y cierra
solo agujeros triangulares simples (bordes de 3 vértices). No inventa
superficies grandes ni garantiza una malla apta para impresión.
"""
import argparse
import json
from collections import Counter, defaultdict, deque
from pathlib import Path

import numpy as np


def leer_obj_triangulos(ruta, max_vertices=500000, max_caras=1000000):
    vertices, caras = [], []
    with Path(ruta).open("r", encoding="utf-8") as archivo:
        for linea in archivo:
            if linea.startswith("v "):
                partes = linea.split()
                if len(partes) != 4 or len(vertices) >= max_vertices:
                    raise ValueError("Vértice OBJ inválido o límite excedido")
                vertices.append([float(x) for x in partes[1:]])
            elif linea.startswith("f "):
                partes = linea.split()[1:]
                if len(partes) != 3 or len(caras) >= max_caras:
                    raise ValueError("Solo se admiten caras triangulares")
                ids = []
                for parte in partes:
                    numero = parte.split("/")[0]
                    if not numero.isdigit() or int(numero) < 1:
                        raise ValueError("Índice OBJ inválido")
                    ids.append(int(numero) - 1)
                caras.append(ids)
            elif linea.strip() and not linea.startswith(("#", "vt ", "vn ", "o ", "g ", "s ", "usemtl ", "mtllib ")):
                raise ValueError("Directiva OBJ no admitida")
    v = np.asarray(vertices, dtype=float).reshape(-1, 3)
    f = np.asarray(caras, dtype=int).reshape(-1, 3)
    if not len(v) or not np.isfinite(v).all() or (len(f) and f.max() >= len(v)):
        raise ValueError("Geometría OBJ inválida")
    return v, f


def reparar_malla(vertices, caras, cerrar_triangulos=True):
    v = np.asarray(vertices, dtype=float)
    f = np.asarray(caras, dtype=int)
    if v.ndim != 2 or v.shape[1] != 3 or not np.isfinite(v).all():
        raise ValueError("Vértices inválidos")
    if f.ndim != 2 or f.shape[1] != 3 or (len(f) and (f.min() < 0 or f.max() >= len(v))):
        raise ValueError("Caras inválidas")
    filtradas, vistas = [], set()
    descartadas = 0
    for cara in f:
        clave = tuple(sorted(map(int, cara)))
        if len(set(clave)) != 3 or clave in vistas:
            descartadas += 1
            continue
        a, b, c = v[cara]
        if np.linalg.norm(np.cross(b-a, c-a)) <= 1e-12:
            descartadas += 1
            continue
        vistas.add(clave)
        filtradas.append([int(i) for i in cara])
    caras_finales = [list(c) for c in filtradas]
    aristas = defaultdict(list)
    for i, (a, b, c) in enumerate(caras_finales):
        for x, y in ((a, b), (b, c), (c, a)):
            aristas[tuple(sorted((x, y)))].append((i, x, y))
    # Propaga orientación usando adyacencia precomputada: O(V + E), no O(F * E).
    adyacencia = defaultdict(list)
    for entradas in aristas.values():
        if len(entradas) != 2:
            continue
        primero, segundo = entradas
        mismo_sentido = (primero[1], primero[2]) == (segundo[1], segundo[2])
        adyacencia[primero[0]].append((segundo[0], mismo_sentido))
        adyacencia[segundo[0]].append((primero[0], mismo_sentido))
    signos = {}
    conflictos = 0
    for inicio in range(len(caras_finales)):
        if inicio in signos:
            continue
        signos[inicio] = 1
        cola = deque([inicio])
        while cola:
            actual = cola.popleft()
            for vecino, mismo_sentido in adyacencia.get(actual, ()):
                esperado = -signos[actual] if mismo_sentido else signos[actual]
                if vecino not in signos:
                    signos[vecino] = esperado
                    cola.append(vecino)
                elif signos[vecino] != esperado:
                    conflictos += 1
    for i, signo in signos.items():
        if signo == -1:
            caras_finales[i][1], caras_finales[i][2] = caras_finales[i][2], caras_finales[i][1]
    aristas_orientadas = defaultdict(list)
    for indice, (a, b, c) in enumerate(caras_finales):
        for x, y in ((a, b), (b, c), (c, a)):
            aristas_orientadas[tuple(sorted((x, y)))].append((indice, x, y))
    agregadas = 0
    if cerrar_triangulos:
        bordes = [clave for clave, entradas in aristas_orientadas.items() if len(entradas) == 1]
        vecinos = defaultdict(set)
        for a, b in bordes:
            vecinos[a].add(b)
            vecinos[b].add(a)
        usados = set()
        for a in sorted(vecinos):
            if len(vecinos[a]) != 2:
                continue
            b, c = sorted(vecinos[a])
            claves = [tuple(sorted(x)) for x in ((a, b), (b, c), (c, a))]
            if any(k in usados or k not in aristas_orientadas or len(aristas_orientadas[k]) != 1 for k in claves):
                continue
            if not (len(vecinos[b]) == len(vecinos[c]) == 2):
                continue
            if tuple(sorted((a, b, c))) in vistas:
                continue
            if np.linalg.norm(np.cross(v[b]-v[a], v[c]-v[a])) <= 1e-12:
                continue
            # Orientar en oposición a la arista de la cara existente.
            x, y = aristas_orientadas[claves[0]][0][1:]
            cara = [a, b, c] if (a, b) != (x, y) else [a, c, b]
            caras_finales.append(cara)
            usados.update(claves)
            agregadas += 1
    cuenta = Counter(tuple(sorted((a, b))) for cara in caras_finales
                    for a, b in ((cara[0], cara[1]), (cara[1], cara[2]), (cara[2], cara[0])))
    informe = {"caras_originales": int(len(f)), "caras_descartadas": descartadas,
               "caras_agregadas": agregadas, "caras_finales": len(caras_finales),
               "aristas_abiertas": sum(n == 1 for n in cuenta.values()),
               "aristas_no_manifold": sum(n > 2 for n in cuenta.values()),
               "conflictos_orientacion": conflictos,
               "malla_cerrada_por_aristas": bool(cuenta) and all(n == 2 for n in cuenta.values()),
               "apto_para_impresion": False}
    return v, np.asarray(caras_finales, dtype=int).reshape(-1, 3), informe


def reparar_obj(entrada, salida):
    from .superficie_nube import guardar_obj
    entrada, salida = Path(entrada).resolve(), Path(salida).resolve()
    informe_ruta = salida.with_suffix(".informe.json")
    if entrada == salida or salida.exists() or informe_ruta.exists():
        raise FileExistsError("Salida o informe ya existente; no sobrescribir")
    v, f = leer_obj_triangulos(entrada)
    v, f, informe = reparar_malla(v, f)
    if not len(f):
        raise ValueError("No quedan caras válidas tras reparar")
    salida.parent.mkdir(parents=True, exist_ok=True)
    guardar_obj(salida, v, f)
    informe_ruta.write_text(json.dumps(informe, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    return informe


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("entrada", type=Path)
    p.add_argument("--salida", type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(reparar_obj(args.entrada, args.salida), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
