"""Procesamiento local en un paso: nube COLMAP PLY -> OBJ reparado -> STL/GLB.

Uso:
 python -m tools.procesar_nube_mvp ruta/modelo_0.ply --salida ruta/salida --alpha 0.05
No sustituye la reconstrucción fotogramétrica de las fotografías.
"""
import argparse
import json
import math
from pathlib import Path

from .colmap_a_malla import nube_colmap_a_malla
from .exportar_formatos_3d import exportar_formatos
from .leer_colmap_ply import leer_nube_colmap_ply
from .reparar_malla import reparar_obj


def procesar_nube_mvp(nube, salida, alpha=None, max_puntos=2500, filtrar_ruido=False):
    from scipy.spatial import cKDTree
    import numpy as np

    nube, salida = Path(nube).resolve(), Path(salida).resolve()
    if not nube.is_file() or nube.suffix.lower() != ".ply":
        raise ValueError("Se requiere una nube COLMAP PLY existente")
    if salida.exists():
        raise FileExistsError("La carpeta de salida ya existe")
    if salida == nube.parent or salida in nube.parents:
        raise ValueError("La salida no puede contener la nube de entrada")
    if type(max_puntos) is not int or max_puntos < 4 or max_puntos > 10000:
        raise ValueError("max_puntos debe estar entre 4 y 10000")
    if alpha is not None and (not math.isfinite(alpha) or alpha <= 0):
        raise ValueError("Alpha inválido")
    puntos = leer_nube_colmap_ply(nube, max_puntos=max_puntos, submuestrear=True)
    if filtrar_ruido:
        from .colmap_a_malla import filtrar_atipicos
        puntos, _ = filtrar_atipicos(puntos)
    puntos = np.unique(puntos, axis=0)
    if len(puntos) < 4:
        raise ValueError("La nube no contiene suficientes puntos distintos")
    if alpha is None:
        distancias, _ = cKDTree(puntos).query(puntos, k=2)
        vecinos = distancias[:, 1]
        vecinos = vecinos[np.isfinite(vecinos) & (vecinos > 0)]
        if len(vecinos) == 0:
            raise ValueError("No se pudo estimar alpha")
        alpha = float(np.median(vecinos) * 3)
    # Escribir en una carpeta nueva, nunca sobrescribir el trabajo previo.
    salida.mkdir(parents=True)
    try:
        original = salida / "original.obj"
        informe_malla = nube_colmap_a_malla(
            nube, original, alpha, max_puntos=max_puntos,
            filtrar_ruido=filtrar_ruido,
        )
        reparada = salida / "reparada.obj"
        informe_reparacion = reparar_obj(original, reparada)
        informe_exportacion = exportar_formatos(
            reparada, salida / "exportados", ("obj", "stl", "glb")
        )
        cerrada = bool(informe_reparacion.get("malla_cerrada_por_aristas"))
        sin_conflictos = (
            informe_reparacion.get("aristas_no_manifold", 0) == 0
            and informe_reparacion.get("conflictos_orientacion", 0) == 0
        )
        respaldo = bool(informe_malla["geometria_de_respaldo"])
        resumen = {
            "calidad_geometrica": (
                "solo_envolvente_convexa" if respaldo else "preliminar_no_validada"
            ),
            "apto_para_impresion": False,
            "control_calidad": {
                "malla_cerrada_por_aristas": cerrada,
                "sin_conflictos_topologicos": sin_conflictos,
                "solo_envolvente_convexa": respaldo,
                "apto_para_impresion": False,
                "requiere_revision_visual": True,
            },
            "nube": str(nube), "alpha_solicitado": alpha,
            "metodo_superficie": informe_malla["metodo_superficie"],
            "geometria_de_respaldo": informe_malla["geometria_de_respaldo"],
            "puntos_procesados": informe_malla["puntos_procesados"],
            "reparacion": informe_reparacion,
            "exportacion": informe_exportacion,
            "advertencia": (
                "La malla es solo una envolvente convexa de respaldo; no representa "
                "concavidades. " if respaldo else ""
            ) + "Escala física no calibrada; revisar visualmente y validar antes de imprimir.",
        }
        (salida / "resumen_mvp.json").write_text(
            json.dumps(resumen, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return resumen
    except Exception as exc:
        # Guardar la causa concreta, además de conservar archivos intermedios.
        (salida / "ERROR.txt").write_text(
            f"Procesamiento incompleto: {type(exc).__name__}: {exc}\n"
            "Revisar los archivos intermedios y no repetir COLMAP.\n",
            encoding="utf-8",
        )
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("nube", type=Path)
    parser.add_argument("--salida", type=Path, required=True)
    parser.add_argument("--alpha", type=float)
    parser.add_argument("--max-puntos", type=int, default=2500)
    parser.add_argument("--filtrar-ruido", action="store_true")
    args = parser.parse_args()
    print(json.dumps(procesar_nube_mvp(args.nube, args.salida, args.alpha,
                                      args.max_puntos, args.filtrar_ruido),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
