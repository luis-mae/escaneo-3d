"""Conecta una nube COLMAP PLY con el mallador alpha-shape existente."""
import argparse
import json
from pathlib import Path

from .leer_colmap_ply import leer_nube_colmap_ply
from .pipeline_superficie import procesar
from .superficie_nube import guardar_obj


def nube_colmap_a_malla(entrada, salida, alpha, max_puntos=200_000):
    entrada, salida = Path(entrada).resolve(), Path(salida).resolve()
    if entrada == salida or salida.exists():
        raise FileExistsError("Salida existente o igual a entrada; no sobrescribir")
    if salida.suffix.lower() != ".obj":
        raise ValueError("La salida debe ser OBJ")
    puntos = leer_nube_colmap_ply(entrada, max_puntos=max_puntos)
    vertices, caras, informe = procesar(puntos, alpha)
    salida.parent.mkdir(parents=True, exist_ok=True)
    guardar_obj(salida, vertices, caras)
    informe.update({"origen": str(entrada), "salida": str(salida),
                    "motor_fotogrametria": "COLMAP",
                    "advertencia": "Malla alpha-shape experimental; sin escala física ni garantía de impresión."})
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
