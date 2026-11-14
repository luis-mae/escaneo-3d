"""Procesamiento experimental de pares consecutivos de una secuencia fotográfica.

Cada par tiene su propio sistema de coordenadas y escala arbitraria.
NO fusionar automáticamente nubes de pares sin registro global.
"""
import argparse
import json
from pathlib import Path

from .fotos_a_modelo import reconstruir_y_exportar


def procesar_secuencia(fotos, focal_px, salida, alpha=None, min_puntos=12,
                      continuar_errores=True):
    rutas = [Path(p) for p in fotos]
    if len(rutas) < 2:
        raise ValueError("Se requieren al menos dos fotografías")
    if len(set(map(str, rutas))) != len(rutas):
        raise ValueError("Hay fotografías repetidas")
    salida = Path(salida)
    if salida.exists() and not salida.is_dir():
        raise NotADirectoryError("La salida debe ser un directorio")
    if (salida / "resumen.json").exists():
        raise FileExistsError("Ya existe resumen.json; elegí otra carpeta")
    # No pisar resultados parciales anteriores.
    for i in range(len(rutas) - 1):
        if (salida / f"par_{i+1:03d}").exists():
            raise FileExistsError("Ya existe un directorio de par; elegí otra carpeta")
    registros = []
    for i, (a, b) in enumerate(zip(rutas[:-1], rutas[1:]), start=1):
        carpeta = salida / f"par_{i:03d}"
        try:
            informe = reconstruir_y_exportar(a, b, focal_px, carpeta, alpha=alpha,
                                            min_puntos=min_puntos)
            registros.append({"par": i, "foto_a": str(a), "foto_b": str(b),
                              "estado": "experimental", "aceptados": informe["aceptados"],
                              "carpeta": str(carpeta)})
        except (ValueError, OSError) as exc:
            registros.append({"par": i, "foto_a": str(a), "foto_b": str(b),
                              "estado": "fallido", "motivo": str(exc)})
            if not continuar_errores:
                break
    resumen = {
        "estado": "pares_independientes_sin_registro_global",
        "total_pares": len(registros),
        "pares_con_nube": sum(r["estado"] == "experimental" for r in registros),
        "pares": registros,
        "advertencia": "Cada par tiene escala y origen arbitrarios: no combinar nubes como si compartieran coordenadas. No es SfM multivista."
    }
    salida.mkdir(parents=True, exist_ok=True)
    (salida / "resumen.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return resumen


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("fotos", nargs="+", type=Path)
    p.add_argument("--focal-px", type=float, required=True)
    p.add_argument("--salida", required=True, type=Path)
    p.add_argument("--alpha", type=float)
    p.add_argument("--min-puntos", type=int, default=12)
    p.add_argument("--detener-en-error", action="store_true")
    args = p.parse_args()
    resumen = procesar_secuencia(args.fotos, args.focal_px, args.salida, args.alpha,
                                args.min_puntos, not args.detener_en_error)
    print(json.dumps(resumen, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
