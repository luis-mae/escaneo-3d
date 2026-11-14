"""Informe reproducible de control de calidad de registros ICP.

Rechaza explícitamente registros con cobertura insuficiente, incluso cuando
el optimizador terminó sin error. No sustituye verificación física.
"""
import argparse
import json
import math
from pathlib import Path
from .registro_icp import registrar_icp


def registrar_con_control(origen, destino, radio, cobertura_minima=0.6, max_iter=30):
    if not isinstance(cobertura_minima, (int, float)) or not math.isfinite(cobertura_minima) or not 0 <= cobertura_minima <= 1:
        raise ValueError("Cobertura mínima fuera de rango")
    resultado = registrar_icp(origen, destino, radio, max_iter=max_iter)
    cobertura = resultado["auditoria_final"]["cobertura_bidireccional"]
    resultado["umbral_cobertura_exigido"] = float(cobertura_minima)
    resultado["aprobado_para_fusion_experimental"] = bool(cobertura >= cobertura_minima)
    if not resultado["aprobado_para_fusion_experimental"]:
        resultado["estado"] = "rechazado_por_cobertura"
    return resultado


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("entrada", type=Path)
    p.add_argument("--salida", type=Path, required=True)
    p.add_argument("--radio", type=float, required=True)
    p.add_argument("--cobertura-minima", type=float, default=0.6)
    args = p.parse_args()
    data = json.loads(args.entrada.read_text(encoding="utf-8"))
    resultado = registrar_con_control(data["origen"], data["destino"], args.radio, args.cobertura_minima)
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
