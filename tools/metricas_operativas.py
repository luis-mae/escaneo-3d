"""Resumen local de tiempos y estados sin datos personales.

Uso: python -m tools.metricas_operativas --datos datos_escaneo
Solo lectura: no envía telemetría, no lee fotografías y no altera proyectos.
"""
import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path

_ID = re.compile(r"^[a-f0-9]{32}$")
_ESTADOS = {"completado", "fallido", "cancelado", "interrumpido", "en_cola", "procesando"}


def resumir(directorio: Path) -> dict:
    """Agrupa registros válidos; no incluye identificadores ni rutas privadas."""
    conteos = Counter()
    duraciones = []
    invalidos = 0
    for archivo in sorted(directorio.glob("*/estado.json")):
        if not _ID.fullmatch(archivo.parent.name) or archivo.is_symlink():
            invalidos += 1
            continue
        try:
            registro = json.loads(archivo.read_text(encoding="utf-8"))
            if not isinstance(registro, dict) or registro.get("id") != archivo.parent.name:
                raise ValueError("ID incompatible")
            estado = registro.get("estado")
            if estado not in _ESTADOS:
                raise ValueError("Estado desconocido")
            conteos[estado] += 1
            # El pipeline puede registrar duración total bajo distintos nombres.
            for clave in ("duracion_total_segundos", "duracion_segundos", "tiempo_total_segundos"):
                valor = registro.get(clave)
                if isinstance(valor, (int, float)) and not isinstance(valor, bool) and math.isfinite(valor) and valor >= 0:
                    duraciones.append(float(valor))
                    break
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            invalidos += 1
    finalizados = sum(conteos[e] for e in ("completado", "fallido", "cancelado"))
    return {
        "proyectos": sum(conteos.values()),
        "por_estado": {k: conteos[k] for k in sorted(_ESTADOS)},
        "finalizados": finalizados,
        "tasa_exito_pct": round(100 * conteos["completado"] / finalizados, 2) if finalizados else None,
        "duraciones_registradas": len(duraciones),
        "duracion_media_segundos": round(sum(duraciones) / len(duraciones), 2) if duraciones else None,
        "registros_invalidos": invalidos,
        "advertencia": "Métricas locales de registros, no certifican reconstrucciones reales ni costos de infraestructura.",
    }


def main():
    parser = argparse.ArgumentParser(description="Métricas operativas locales y anónimas de Escaneo3D")
    parser.add_argument("--datos", type=Path, default=Path("datos_escaneo"))
    parser.add_argument("--salida", type=Path, help="Guardar JSON en una ruta elegida")
    args = parser.parse_args()
    resultado = json.dumps(resumir(args.datos), ensure_ascii=False, indent=2) + "\n"
    if args.salida:
        args.salida.write_text(resultado, encoding="utf-8")
    else:
        print(resultado, end="")


if __name__ == "__main__":
    main()
