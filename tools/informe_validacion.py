"""Resume errores dimensionales de una campaña de validación con medidas patrón.

No mide la malla: procesa mediciones introducidas por el operador y conserva
la incertidumbre declarada. No certifica precisión ni aptitud de fabricación.
"""
import argparse
import json
import math
from pathlib import Path


def analizar_mediciones(datos, tolerancia_pct=5.0):
    if not isinstance(datos, dict) or not isinstance(datos.get("objetos"), list):
        raise ValueError("Se requiere un objeto JSON con una lista 'objetos'")
    if not math.isfinite(tolerancia_pct) or tolerancia_pct <= 0 or tolerancia_pct > 100:
        raise ValueError("La tolerancia debe ser mayor que 0 y no superar 100%")
    resultados = []
    errores_globales = []
    for objeto in datos["objetos"]:
        if not isinstance(objeto, dict) or not isinstance(objeto.get("mediciones"), list):
            raise ValueError("Cada objeto debe contener una lista de mediciones")
        nombre = str(objeto.get("nombre", "")).strip()
        if not nombre or not objeto["mediciones"]:
            raise ValueError("Cada objeto necesita nombre y al menos una medición")
        mediciones = []
        for medicion in objeto["mediciones"]:
            try:
                referencia = float(medicion["referencia_mm"])
                observada = float(medicion["medida_mm"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError("Cada medición requiere referencia_mm y medida_mm") from exc
            if not math.isfinite(referencia) or not math.isfinite(observada) or referencia <= 0 or observada <= 0:
                raise ValueError("Las medidas deben ser positivas y finitas")
            error_mm = observada - referencia
            error_pct = abs(error_mm) / referencia * 100
            errores_globales.append(error_pct)
            mediciones.append({
                "referencia_mm": referencia,
                "medida_mm": observada,
                "error_mm": error_mm,
                "error_absoluto_pct": error_pct,
                "dentro_tolerancia": error_pct <= tolerancia_pct,
                "incertidumbre_instrumento_mm": medicion.get("incertidumbre_instrumento_mm"),
            })
        resultados.append({
            "nombre": nombre,
            "mediciones": mediciones,
            "error_maximo_pct": max(m["error_absoluto_pct"] for m in mediciones),
            "error_medio_pct": sum(m["error_absoluto_pct"] for m in mediciones) / len(mediciones),
            "dentro_tolerancia": all(m["dentro_tolerancia"] for m in mediciones),
        })
    if not resultados:
        raise ValueError("No hay objetos para analizar")
    return {
        "objetos_analizados": len(resultados),
        "mediciones_analizadas": len(errores_globales),
        "tolerancia_pct": tolerancia_pct,
        "error_maximo_global_pct": max(errores_globales),
        "error_medio_global_pct": sum(errores_globales) / len(errores_globales),
        "objetos_dentro_tolerancia": sum(r["dentro_tolerancia"] for r in resultados),
        "resultados": resultados,
        "advertencia": "Análisis de medidas introducidas por el operador. No certifica precisión, escala, geometría ni aptitud de fabricación.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entrada", type=Path, help="JSON con objetos y mediciones")
    parser.add_argument("--tolerancia-pct", type=float, default=5.0)
    parser.add_argument("--salida", type=Path, required=True)
    args = parser.parse_args()
    datos = json.loads(args.entrada.read_text(encoding="utf-8"))
    informe = analizar_mediciones(datos, args.tolerancia_pct)
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(informe, ensure_ascii=False, indent=2) + "\\n",
                           encoding="utf-8")
    print(json.dumps(informe, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
