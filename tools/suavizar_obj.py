"""Suavizado conservador de OBJ triangulares con bordes protegidos."""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from .reparar_malla import leer_obj_triangulos
from .superficie_nube import guardar_obj


def suavizar(vertices, caras, iteraciones=2, intensidad=0.25):
    v = np.asarray(vertices, dtype=float)
    f = np.asarray(caras, dtype=int)
    if v.ndim != 2 or v.shape[1] != 3 or not np.isfinite(v).all():
        raise ValueError("Vértices inválidos")
    if f.ndim != 2 or f.shape[1] != 3 or not len(f) or f.min() < 0 or f.max() >= len(v):
        raise ValueError("Caras inválidas")
    if type(iteraciones) is not int or not 0 <= iteraciones <= 100:
        raise ValueError("Iteraciones inválidas")
    if not np.isfinite(intensidad) or not 0 <= intensidad <= 0.5:
        raise ValueError("Intensidad inválida")
    aristas = Counter(tuple(sorted((int(a), int(b))))
                      for cara in f for a, b in ((cara[0], cara[1]),
                                                  (cara[1], cara[2]),
                                                  (cara[2], cara[0])))
    bordes = {x for (a, b), n in aristas.items() if n != 2 for x in (a, b)}
    vecinos = defaultdict(set)
    for a, b in aristas:
        vecinos[a].add(b)
        vecinos[b].add(a)
    v = v.copy()
    for _ in range(iteraciones):
        nuevo = v.copy()
        for i, adyacentes in vecinos.items():
            if i not in bordes:
                nuevo[i] = v[i] + intensidad * (v[list(adyacentes)].mean(axis=0) - v[i])
        v = nuevo
    informe = {"vertices": len(v), "caras": len(f),
               "vertices_protegidos": len(bordes),
               "aristas_abiertas": sum(n == 1 for n in aristas.values()),
               "aristas_no_manifold": sum(n > 2 for n in aristas.values()),
               "iteraciones": iteraciones, "intensidad": intensidad,
               "apto_para_impresion": False,
               "advertencia": "Suavizado experimental: puede alterar dimensiones y detalles."}
    return v, f.copy(), informe


def suavizar_obj(entrada, salida, iteraciones=2, intensidad=0.25):
    entrada, salida = Path(entrada).resolve(), Path(salida).resolve()
    informe_path = salida.with_suffix(".informe.json")
    if entrada == salida or salida.exists() or informe_path.exists():
        raise FileExistsError("No sobrescribir entrada, salida ni informe")
    if salida.suffix.lower() != ".obj":
        raise ValueError("Salida OBJ requerida")
    v, f = leer_obj_triangulos(entrada)
    v, f, informe = suavizar(v, f, iteraciones, intensidad)
    salida.parent.mkdir(parents=True, exist_ok=True)
    guardar_obj(salida, v, f)
    informe_path.write_text(json.dumps(informe, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    return informe


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("entrada", type=Path)
    p.add_argument("--salida", type=Path, required=True)
    p.add_argument("--iteraciones", type=int, default=2)
    p.add_argument("--intensidad", type=float, default=0.25)
    args = p.parse_args()
    print(json.dumps(suavizar_obj(args.entrada, args.salida,
                                  args.iteraciones, args.intensidad),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
