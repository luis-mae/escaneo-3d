"""Flujo experimental fotos -> nube PLY -> malla OBJ opcional.

La reconstrucción de dos vistas produce escala arbitraria; no equivale a CAD.
"""
import argparse
import json
import tempfile
from pathlib import Path

import numpy as np

from .nube_dos_vistas import reconstruir_par, guardar_ply
from .pipeline_superficie import procesar
from .superficie_nube import guardar_obj


def reconstruir_y_exportar(foto_a, foto_b, focal_px, salida, alpha=None,
                          min_puntos=12, sobrescribir=False):
    salida = Path(salida)
    if not np.isfinite(focal_px) or focal_px <= 0:
        raise ValueError("La focal debe ser positiva y finita")
    if alpha is not None and (not np.isfinite(alpha) or alpha <= 0):
        raise ValueError("Alpha debe ser positivo y finito")
    resultado = reconstruir_par(foto_a, foto_b, focal_px, min_puntos=min_puntos)
    if resultado["estado"] != "experimental" or resultado.get("aceptados", 0) < min_puntos:
        raise ValueError("Reconstrucción insuficiente: " + resultado.get("motivo", "pocos puntos válidos"))
    puntos = np.asarray(resultado["puntos"], dtype=float)
    if puntos.ndim != 2 or puntos.shape[1] != 3 or not np.isfinite(puntos).all():
        raise ValueError("La reconstrucción produjo puntos inválidos")
    nombres = ["nube.ply", "informe.json"]
    if alpha is not None:
        nombres.extend(["superficie.obj", "superficie.informe.json"])
    if salida.exists() and not salida.is_dir():
        raise NotADirectoryError("La salida debe ser un directorio")
    if not sobrescribir and any((salida / n).exists() for n in nombres):
        raise FileExistsError("Ya existe una exportación; usar --sobrescribir")
    salida.mkdir(parents=True, exist_ok=True)
    informe = {k: v for k, v in resultado.items() if k != "puntos"}
    informe.update({"foto_a": str(foto_a), "foto_b": str(foto_b),
                    "focal_px": float(focal_px), "escala": "arbitraria",
                    "malla": "experimental" if alpha is not None else "no solicitada"})
    with tempfile.TemporaryDirectory(prefix=".fotos_tmp_", dir=salida) as tmp:
        tmp = Path(tmp)
        guardar_ply(puntos, tmp / "nube.ply")
        if alpha is not None:
            vertices, caras, diagnostico = procesar(puntos, alpha)
            guardar_obj(tmp / "superficie.obj", vertices, caras)
            (tmp / "superficie.informe.json").write_text(
                json.dumps(diagnostico, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            informe["superficie"] = diagnostico
        (tmp / "informe.json").write_text(
            json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        # Preparar todos los artefactos antes de moverlos al destino.
        import os
        for nombre in nombres:
            os.replace(tmp / nombre, salida / nombre)
    return informe


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("foto_a", type=Path)
    p.add_argument("foto_b", type=Path)
    p.add_argument("--focal-px", type=float, required=True)
    p.add_argument("--salida", type=Path, required=True)
    p.add_argument("--alpha", type=float, help="Malla alpha-shape opcional; requiere nube adecuada")
    p.add_argument("--min-puntos", type=int, default=12)
    p.add_argument("--sobrescribir", action="store_true")
    args = p.parse_args()
    if args.min_puntos < 8:
        p.error("--min-puntos debe ser >= 8")
    informe = reconstruir_y_exportar(
        args.foto_a, args.foto_b, args.focal_px, args.salida, args.alpha,
        args.min_puntos, args.sobrescribir)
    print(json.dumps(informe, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
