"""Estimación local de costos por reconstrucción, sin cobros ni servicios externos.

Ejemplo: python -m tools.estimador_costos --segundos 1200 --precio-hora 0.25
"""
import argparse
import json
import math


def estimar(segundos: float, precio_hora: float, almacenamiento_gb: float = 0,
            precio_gb_mes: float = 0, transferencia_gb: float = 0,
            precio_transferencia_gb: float = 0) -> dict:
    valores = (segundos, precio_hora, almacenamiento_gb, precio_gb_mes,
               transferencia_gb, precio_transferencia_gb)
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or
           not math.isfinite(v) or v < 0 for v in valores):
        raise ValueError("Los parámetros deben ser números finitos no negativos")
    computo = segundos / 3600 * precio_hora
    almacenamiento = almacenamiento_gb * precio_gb_mes
    transferencia = transferencia_gb * precio_transferencia_gb
    return {
        "computo": round(computo, 6),
        "almacenamiento_mes": round(almacenamiento, 6),
        "transferencia": round(transferencia, 6),
        "total_estimado": round(computo + almacenamiento + transferencia, 6),
        "moneda": "unidad monetaria configurada por el operador",
        "advertencia": "Estimación manual; no mide consumo real ni constituye precio de venta.",
    }


def main():
    parser = argparse.ArgumentParser(description="Estimación de costos de un trabajo 3D")
    parser.add_argument("--segundos", type=float, required=True)
    parser.add_argument("--precio-hora", type=float, required=True)
    parser.add_argument("--almacenamiento-gb", type=float, default=0)
    parser.add_argument("--precio-gb-mes", type=float, default=0)
    parser.add_argument("--transferencia-gb", type=float, default=0)
    parser.add_argument("--precio-transferencia-gb", type=float, default=0)
    args = parser.parse_args()
    print(json.dumps(estimar(args.segundos, args.precio_hora, args.almacenamiento_gb,
                            args.precio_gb_mes, args.transferencia_gb,
                            args.precio_transferencia_gb), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
