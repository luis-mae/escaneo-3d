"""Reconstrucción densa opcional COLMAP desde modelo sparse existente.

No recalcula SIFT/matching/mapper. CPU sin CUDA puede ser lento y consumir RAM.
"""
import argparse
import json
import shutil
import subprocess
import time
from pathlib import Path

from .motor_colmap import _ply_con_vertices
from .proceso_controlado import ejecutar_comando


def densificar_colmap(fotos, modelo_sparse, salida, colmap="colmap",
                      usar_gpu=False, timeout_segundos=14400, cancel_event=None):
    fotos, modelo, salida = (Path(p).resolve() for p in (fotos, modelo_sparse, salida))
    if not fotos.is_dir():
        raise ValueError("Carpeta de fotografías inexistente")
    if not all((modelo / f).is_file() for f in ("cameras.bin", "images.bin", "points3D.bin")):
        raise ValueError("Modelo sparse incompleto: faltan archivos .bin")
    if salida.exists():
        raise FileExistsError("La salida densa ya existe; no se sobrescribe")
    if salida == fotos or salida == modelo or salida in fotos.parents or salida in modelo.parents or fotos in salida.parents or modelo in salida.parents:
        raise ValueError("La salida debe ser independiente de las entradas")
    if type(timeout_segundos) is not int or timeout_segundos <= 0:
        raise ValueError("Timeout inválido")
    ejecutable = shutil.which(colmap)
    if not ejecutable:
        raise FileNotFoundError("COLMAP no encontrado en PATH")
    salida.mkdir(parents=True)
    registros = []
    limite = time.monotonic() + timeout_segundos
    pasos = [
        ("image_undistorter", [
            "--image_path", str(fotos), "--input_path", str(modelo),
            "--output_path", str(salida), "--output_type", "COLMAP",
        ]),
        ("patch_match_stereo", [
            "--workspace_path", str(salida), "--workspace_format", "COLMAP",
            "--PatchMatchStereo.geom_consistency", "true",
            "--PatchMatchStereo.gpu_index", "0" if usar_gpu else "-1",
        ]),
        ("stereo_fusion", [
            "--workspace_path", str(salida), "--workspace_format", "COLMAP",
            "--input_type", "geometric", "--output_path", str(salida / "fused.ply"),
        ]),
    ]
    try:
        for nombre, argumentos in pasos:
            restante = limite - time.monotonic()
            if restante <= 0:
                raise TimeoutError("Tiempo total agotado antes de " + nombre)
            inicio = time.monotonic()
            try:
                proceso = ejecutar_comando(
                    [ejecutable, nombre, *argumentos], restante,
                    cancel_event=cancel_event,
                )
            except subprocess.TimeoutExpired as exc:
                registros.append({"paso": nombre, "estado": "timeout"})
                raise TimeoutError("COLMAP agotó el tiempo en " + nombre) from exc
            registros.append({
                "paso": nombre, "codigo": proceso.returncode,
                "segundos": round(time.monotonic() - inicio, 2),
                "stderr_final": proceso.stderr[-2000:],
            })
            if proceso.returncode != 0:
                raise RuntimeError("COLMAP falló en " + nombre + ": " + proceso.stderr[-400:])
        nube = salida / "fused.ply"
        if not nube.is_file() or not _ply_con_vertices(nube):
            raise RuntimeError("COLMAP terminó pero fused.ply no tiene puntos válidos")
        estado = "nube_densa_generada"
    except Exception as exc:
        estado = "incompleto"
        error = type(exc).__name__ + ": " + str(exc)
        (salida / "ERROR_DENSO.txt").write_text(error + "\n", encoding="utf-8")
        raise
    finally:
        informe = {
            "estado": locals().get("estado", "incompleto"),
            "fotos": str(fotos), "modelo_sparse": str(modelo),
            "nube_densa": str(salida / "fused.ply"),
            "pasos": registros, "gpu_solicitada": bool(usar_gpu),
            "advertencia": "Nube densa sin escala física calibrada; inspeccionar forma antes de imprimir.",
        }
        (salida / "informe_denso.json").write_text(
            json.dumps(informe, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return informe


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fotos", required=True, type=Path)
    p.add_argument("--sparse", required=True, type=Path)
    p.add_argument("--salida", required=True, type=Path)
    p.add_argument("--colmap", default="colmap")
    p.add_argument("--gpu", action="store_true")
    p.add_argument("--timeout", type=int, default=14400)
    args = p.parse_args()
    print(json.dumps(densificar_colmap(
        args.fotos, args.sparse, args.salida, args.colmap,
        args.gpu, args.timeout,
    ), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
