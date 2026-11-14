"""Reconstrucción densa COLMAP (undistorter, PatchMatch y fusión).

Requiere GPU CUDA para PatchMatch en instalaciones habituales de COLMAP.
La nube fusionada no es una malla cerrada ni posee escala métrica.
"""
import argparse
import json
import shutil
import subprocess
import time
from pathlib import Path

from .proceso_controlado import ejecutar_comando


def densificar_colmap(carpeta_resultado, carpeta_fotos, modelo="0",
                      ejecutable="colmap", timeout_segundos=14400, cancel_event=None):
    raiz = Path(carpeta_resultado).resolve()
    fotos = Path(carpeta_fotos).resolve()
    sparse = raiz / "sparse" / str(modelo)
    if not fotos.is_dir() or not sparse.is_dir():
        raise ValueError("Faltan imágenes o modelo disperso COLMAP")
    if not all((sparse / n).is_file() for n in
               ("cameras.bin", "images.bin", "points3D.bin")):
        raise ValueError("Modelo COLMAP incompleto")
    if type(timeout_segundos) is not int or timeout_segundos <= 0:
        raise ValueError("Timeout inválido")
    binario = shutil.which(ejecutable)
    if not binario:
        raise FileNotFoundError("COLMAP no está instalado o no está en PATH")
    espacio = raiz / ("dense_" + str(modelo))
    if espacio.exists():
        raise FileExistsError("Ya existe la carpeta densa; no se sobrescribe")
    if fotos == espacio or espacio in fotos.parents or fotos in espacio.parents:
        raise ValueError("Carpetas de entrada y salida superpuestas")
    espacio.mkdir(parents=True)
    salida_ply = espacio / "fused.ply"
    pasos = [
        ("image_undistorter", ["--image_path", str(fotos), "--input_path", str(sparse),
                               "--output_path", str(espacio), "--output_type", "COLMAP"]),
        ("patch_match_stereo", ["--workspace_path", str(espacio),
                                "--workspace_format", "COLMAP",
                                "--PatchMatchStereo.geom_consistency", "true"]),
        ("stereo_fusion", ["--workspace_path", str(espacio),
                           "--workspace_format", "COLMAP",
                           "--input_type", "geometric",
                           "--output_path", str(salida_ply)]),
    ]
    registro = []
    limite_global = time.monotonic() + timeout_segundos
    for nombre, opciones in pasos:
        restante = min(timeout_segundos, limite_global - time.monotonic())
        if restante <= 0:
            registro.append({"paso": nombre, "error": "presupuesto_total_agotado"})
            break
        try:
            proceso = ejecutar_comando([binario, nombre, *opciones], restante, cancel_event=cancel_event)
            registro.append({"paso": nombre, "codigo": proceso.returncode,
                             "stderr_final": proceso.stderr[-2500:]})
        except subprocess.TimeoutExpired:
            registro.append({"paso": nombre, "error": "tiempo_agotado"})
        if registro[-1].get("codigo") != 0:
            break
    valido = (len(registro) == len(pasos) and
              all(p.get("codigo") == 0 for p in registro) and
              salida_ply.is_file() and salida_ply.stat().st_size > 0)
    informe = {"motor": "COLMAP", "tipo": "nube_densa",
               "estado": "completado" if valido else "incompleto",
               "archivo_ply": str(salida_ply) if valido else None,
               "pasos": registro, "presupuesto_total_segundos": timeout_segundos,
               "advertencia": "Nube densa sin escala métrica; no es una malla cerrada."}
    (espacio / "informe_denso.json").write_text(
        json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not valido:
        raise RuntimeError("Reconstrucción densa fallida; consultar informe_denso.json")
    return informe


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("resultado", type=Path)
    p.add_argument("fotos", type=Path)
    p.add_argument("--modelo", default="0")
    p.add_argument("--colmap", default="colmap")
    p.add_argument("--timeout", type=int, default=14400)
    args = p.parse_args()
    print(json.dumps(densificar_colmap(args.resultado, args.fotos, args.modelo,
                                      args.colmap, args.timeout),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
