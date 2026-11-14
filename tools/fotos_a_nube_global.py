"""Reconstrucción dispersa experimental de fotografías a nube 3D global.

No calcula escala métrica ni produce mallas listas para imprimir.
"""
import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

import cv2
import numpy as np

from .tracks_desde_fotos import extraer_tracks
from .sfm_incremental import reconstruir_tracks
from .nube_dos_vistas import guardar_ply
from .calidad_sfm import evaluar_calidad_sfm


def fotos_a_nube(fotos, focal_px, salida, min_inliers=12, max_features=3000, exigir_calidad=False):
    rutas = [Path(p) for p in fotos]
    if len(rutas) < 2 or len({str(p.resolve()) for p in rutas}) != len(rutas):
        raise ValueError("Se requieren al menos dos fotografías distintas")
    if type(min_inliers) is not int or min_inliers < 8:
        raise ValueError("min_inliers inválido")
    if not np.isfinite(focal_px) or focal_px <= 0:
        raise ValueError("Focal inválida")
    dimensiones = []
    for ruta in rutas:
        imagen = cv2.imread(str(ruta), cv2.IMREAD_GRAYSCALE)
        if imagen is None:
            raise ValueError(f"Fotografía ilegible: {ruta}")
        dimensiones.append(tuple(imagen.shape))
    if len(set(dimensiones)) != 1:
        raise ValueError("Todas las fotografías deben tener la misma resolución")
    alto, ancho = dimensiones[0]
    salida = Path(salida)
    if salida.exists() and not salida.is_dir():
        raise NotADirectoryError("Salida inválida")
    nombres = ["nube.ply", "informe.json", "tracks.json"]
    if any((salida / n).exists() for n in nombres):
        raise FileExistsError("La salida contiene archivos existentes")
    tracks = extraer_tracks(rutas, max_features=max_features, min_inliers=min_inliers)
    sfm = reconstruir_tracks(tracks, focal_px, ancho, alto, min_inliers=min_inliers)
    sfm["control_calidad"] = evaluar_calidad_sfm(sfm, min_puntos=min_inliers)
    if sfm["puntos_3d"] < min_inliers:
        raise ValueError("No se reconstruyeron suficientes puntos 3D")
    if exigir_calidad and not sfm["control_calidad"]["aprobado_para_inspeccion_experimental"]:
        fallos = [nombre for nombre, ok in sfm["control_calidad"]["criterios"].items() if not ok]
        raise ValueError("Control de calidad no superado: " + ", ".join(fallos))
    salida.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".sfm_tmp_", dir=salida) as temporal:
        tmp = Path(temporal)
        guardar_ply(sfm["puntos"], tmp / "nube.ply")
        (tmp / "tracks.json").write_text(
            json.dumps(tracks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        informe = {k: v for k, v in sfm.items() if k != "puntos"}
        informe.update({"fotos": [str(p) for p in rutas], "ancho": ancho,
                        "alto": alto, "focal_px": float(focal_px),
                        "sha256_ply": hashlib.sha256((tmp / "nube.ply").read_bytes()).hexdigest(),
                        "sha256_tracks": hashlib.sha256((tmp / "tracks.json").read_bytes()).hexdigest()})
        (tmp / "informe.json").write_text(
            json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for nombre in nombres:
            os.replace(tmp / nombre, salida / nombre)
    return informe


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("fotos", nargs="+", type=Path)
    p.add_argument("--focal-px", required=True, type=float)
    p.add_argument("--salida", required=True, type=Path)
    p.add_argument("--min-inliers", type=int, default=12)
    p.add_argument("--max-features", type=int, default=3000)
    p.add_argument("--exigir-calidad", action="store_true",
                   help="No exportar si falla algún umbral interno de consistencia")
    args = p.parse_args()
    resultado = fotos_a_nube(args.fotos, args.focal_px, args.salida,
                            args.min_inliers, args.max_features, args.exigir_calidad)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
