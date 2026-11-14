"""Selección automática preliminar de alpha para nubes COLMAP.

Estima espaciamiento local y prueba radios crecientes, conservando el
primer resultado con caras. No certifica geometría ni escala física.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from .leer_colmap_ply import leer_nube_colmap_ply
from .pipeline_superficie import procesar
from .superficie_nube import guardar_obj


def reconstruir_superficie_auto(entrada, salida, max_puntos=12000,
                               factores=(2.0, 3.5, 6.0, 10.0)):
    entrada, salida = Path(entrada).resolve(), Path(salida).resolve()
    if entrada == salida or salida.exists() or salida.suffix.lower() != ".obj":
        raise ValueError("La salida debe ser OBJ, distinta y no existente")
    if type(max_puntos) is not int or max_puntos < 4:
        raise ValueError("max_puntos debe ser entero >= 4")
    puntos = leer_nube_colmap_ply(entrada, max_puntos=2_000_000)
    total = len(puntos)
    if total > max_puntos:
        # Muestreo determinista sin reemplazo para limitar costo Delaunay.
        indices = np.linspace(0, total - 1, max_puntos, dtype=np.int64)
        puntos = puntos[indices]
    puntos = np.unique(puntos, axis=0)
    if len(puntos) < 4:
        raise ValueError("Insuficientes puntos distintos")
    distancias, _ = cKDTree(puntos).query(puntos, k=2)
    vecinos = distancias[:, 1]
    positivos = vecinos[np.isfinite(vecinos) & (vecinos > 0)]
    if len(positivos) == 0:
        raise ValueError("No se puede estimar separación entre puntos")
    base = float(np.median(positivos))
    intentos = []
    elegido = None
    for factor in factores:
        if not np.isfinite(factor) or factor <= 0:
            raise ValueError("Factores alpha inválidos")
        alpha = base * float(factor)
        try:
            vertices, caras, informe = procesar(puntos, alpha)
            intentos.append({"alpha": alpha, "caras": int(len(caras)),
                             "cerrada_por_aristas": informe["malla_cerrada_por_aristas"]})
            if elegido is None:
                elegido = (vertices, caras, informe, alpha)
            if informe["malla_cerrada_por_aristas"]:
                elegido = (vertices, caras, informe, alpha)
                break
        except ValueError as exc:
            intentos.append({"alpha": alpha, "error": str(exc)})
    if elegido is None:
        raise ValueError("No se pudo generar superficie con los radios probados")
    vertices, caras, informe, alpha = elegido
    salida.parent.mkdir(parents=True, exist_ok=True)
    guardar_obj(salida, vertices, caras)
    informe.update({"metodo": "alpha_automatico_experimental",
                    "alpha_seleccionado": alpha, "separacion_mediana": base,
                    "puntos_originales": total, "puntos_utilizados": len(puntos),
                    "intentos": intentos,
                    "advertencia": "Alpha automático experimental. Revisar concavidades, orientación, unidades y topología; no apto para impresión sin validar."})
    salida.with_suffix(".informe.json").write_text(
        json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return informe


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("entrada", type=Path)
    p.add_argument("--salida", type=Path, required=True)
    p.add_argument("--max-puntos", type=int, default=12000)
    args = p.parse_args()
    print(json.dumps(reconstruir_superficie_auto(args.entrada, args.salida,
                                                args.max_puntos),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
