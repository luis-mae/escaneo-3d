"""Exporta modelos dispersos COLMAP a PLY mediante model_converter.

Requiere COLMAP instalado y un modelo SfM previamente generado.
"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path


def exportar_modelos_colmap(carpeta_sfm, ejecutable="colmap", timeout_segundos=600):
    raiz = Path(carpeta_sfm).resolve()
    sparse = raiz / "sparse"
    if not sparse.is_dir():
        raise ValueError("No existe la carpeta sparse de COLMAP")
    if not isinstance(timeout_segundos, int) or timeout_segundos <= 0:
        raise ValueError("Timeout inválido")
    binario = shutil.which(ejecutable)
    if binario is None:
        raise FileNotFoundError("COLMAP no está disponible en PATH")
    modelos = sorted(
        p for p in sparse.iterdir()
        if p.is_dir() and all((p / n).is_file()
                              for n in ("cameras.bin", "images.bin", "points3D.bin"))
    )
    if not modelos:
        raise ValueError("No hay modelos COLMAP dispersos válidos")
    resultados = []
    for modelo in modelos:
        salida = raiz / ("modelo_" + modelo.name + ".ply")
        if salida.exists():
            resultados.append({"modelo": modelo.name, "estado": "ya_existe",
                               "ply": str(salida)})
            continue
        comando = [binario, "model_converter", "--input_path", str(modelo),
                   "--output_path", str(salida), "--output_type", "PLY"]
        try:
            proceso = subprocess.run(comando, capture_output=True, text=True,
                                     timeout=timeout_segundos, check=False)
            correcto = proceso.returncode == 0 and salida.is_file() and salida.stat().st_size > 0
            resultados.append({"modelo": modelo.name,
                               "estado": "exportado" if correcto else "fallo",
                               "ply": str(salida) if correcto else None,
                               "codigo": proceso.returncode,
                               "stderr_final": proceso.stderr[-2000:]})
        except subprocess.TimeoutExpired:
            resultados.append({"modelo": modelo.name, "estado": "tiempo_agotado"})
    informe = {"motor": "COLMAP", "exportaciones": resultados,
               "advertencia": "PLY disperso en escala arbitraria; no es malla imprimible."}
    (raiz / "informe_exportacion_colmap.json").write_text(
        json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return informe


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("carpeta_sfm", type=Path)
    p.add_argument("--colmap", default="colmap")
    p.add_argument("--timeout", type=int, default=600)
    args = p.parse_args()
    print(json.dumps(exportar_modelos_colmap(args.carpeta_sfm, args.colmap,
                                             args.timeout), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
