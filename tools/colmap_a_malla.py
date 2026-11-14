"""Conecta una nube COLMAP PLY con el mallador alpha-shape existente."""
import argparse
import json
from pathlib import Path
from scipy.spatial import QhullError

from .leer_colmap_ply import leer_nube_colmap_ply
from .pipeline_superficie import procesar
from .superficie_nube import generar_superficie
from .superficie_nube import guardar_obj


def nube_colmap_a_malla(entrada, salida, alpha, max_puntos=50_000, submuestrear=True):
    entrada, salida = Path(entrada).resolve(), Path(salida).resolve()
    if entrada == salida or salida.exists():
        raise FileExistsError("Salida existente o igual a entrada; no sobrescribir")
    if salida.suffix.lower() != ".obj":
        raise ValueError("La salida debe ser OBJ")
    puntos = leer_nube_colmap_ply(entrada, max_puntos=max_puntos,
                                  submuestrear=submuestrear)
    # El mallado tetraédrico exige cuatro puntos geométricamente distintos.
    import numpy as np
    puntos = np.unique(puntos, axis=0)
    if len(puntos) < 4:
        raise ValueError("La nube no contiene cuatro puntos 3D distintos")
    try:
        vertices, caras, informe = procesar(puntos, alpha)
        informe["metodo_superficie"] = "alpha_shape"
    except (ValueError, RuntimeError, MemoryError, QhullError) as exc:
        # Una nube dispersa puede carecer de densidad para alpha-shape.
        # Entregar una vista OBJ preliminar sin fingir una superficie detallada.
        vertices, caras, volumen = generar_superficie(puntos)
        informe = {
            "vertices": int(len(vertices)), "caras": int(len(caras)),
            "metodo_superficie": "envolvente_convexa_respaldo",
            "motivo_respaldo": str(exc)[:300],
            "volumen_unidades_arbitrarias": volumen,
            "apto_para_impresion": False,
            "advertencia": "Envolvente convexa aproximada: no conserva concavidades ni detalles.",
        }
    if not len(caras):
        raise ValueError("No se pudo construir ninguna cara para la malla OBJ")
    salida.parent.mkdir(parents=True, exist_ok=True)
    guardar_obj(salida, vertices, caras)
    informe.update({"origen": str(entrada), "salida": str(salida),
                    "motor_fotogrametria": "COLMAP",
                    "puntos_procesados": len(puntos),
                    "submuestreo_determinista": bool(submuestrear)})
    salida.with_suffix(".informe.json").write_text(
        json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return informe


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("entrada", type=Path, help="fused.ply o modelo_0.ply de COLMAP")
    p.add_argument("--salida", required=True, type=Path)
    p.add_argument("--alpha", required=True, type=float)
    p.add_argument("--max-puntos", type=int, default=200_000)
    args = p.parse_args()
    print(json.dumps(nube_colmap_a_malla(args.entrada, args.salida, args.alpha,
                                        args.max_puntos), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
