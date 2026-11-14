"""Adaptador experimental para ejecutar COLMAP instalado localmente.

COLMAP es una dependencia externa GPL; no se distribuye ni instala aquí.
Requiere ejecutable colmap disponible en PATH y fotografías locales.
"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path


def ejecutar_colmap(fotos_dir, salida, ejecutable="colmap", usar_gpu=False,
                    timeout_segundos=7200):
    fotos = Path(fotos_dir).resolve()
    destino = Path(salida).resolve()
    if not fotos.is_dir() or not any(
        p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}
        for p in fotos.iterdir()
    ):
        raise ValueError("Se requiere carpeta con fotografías JPG/PNG")
    if destino == fotos or destino in fotos.parents or fotos in destino.parents:
        raise ValueError("La salida debe estar separada de las fotografías")
    if destino.exists():
        raise FileExistsError("La salida ya existe; no se sobrescriben resultados")
    if not isinstance(timeout_segundos, int) or timeout_segundos <= 0:
        raise ValueError("Timeout inválido")
    binario = shutil.which(ejecutable)
    if binario is None:
        raise FileNotFoundError("COLMAP no está instalado o no está en PATH")
    destino.mkdir(parents=True)
    base = destino / "database.db"
    sparse = destino / "sparse"
    sparse.mkdir()
    pasos = [
        ("feature_extractor", ["--database_path", str(base),
                               "--image_path", str(fotos),
                               "--ImageReader.single_camera", "1",
                               "--SiftExtraction.use_gpu", str(int(usar_gpu))]),
        ("exhaustive_matcher", ["--database_path", str(base),
                                "--SiftMatching.use_gpu", str(int(usar_gpu))]),
        ("mapper", ["--database_path", str(base),
                    "--image_path", str(fotos), "--output_path", str(sparse)]),
    ]
    registro = []
    for nombre, opciones in pasos:
        comando = [binario, nombre, *opciones]
        try:
            proceso = subprocess.run(comando, capture_output=True, text=True,
                                     timeout=timeout_segundos, check=False)
            entrada = {"paso": nombre, "codigo": proceso.returncode,
                       "stdout_final": proceso.stdout[-3000:],
                       "stderr_final": proceso.stderr[-3000:]}
        except subprocess.TimeoutExpired:
            entrada = {"paso": nombre, "error": "tiempo_agotado"}
        registro.append(entrada)
        if entrada.get("codigo") != 0:
            break
    modelos = sorted(str(p.relative_to(destino)) for p in sparse.iterdir()
                     if p.is_dir() and (p / "cameras.bin").exists()
                     and (p / "images.bin").exists() and (p / "points3D.bin").exists())
    estado = "reconstruccion_dispersa" if modelos and len(registro) == 3 and all(
        p.get("codigo") == 0 for p in registro) else "incompleto"
    exportaciones = []
    if estado == "reconstruccion_dispersa":
        for indice, relativo in enumerate(modelos):
            ruta_ply = destino / f"modelo_{indice:03d}.ply"
            try:
                proceso = subprocess.run(
                    [binario, "model_converter", "--input_path", str(destino / relativo),
                     "--output_path", str(ruta_ply), "--output_type", "PLY"],
                    capture_output=True, text=True, timeout=timeout_segundos, check=False)
                valido = (proceso.returncode == 0 and ruta_ply.is_file()
                          and ruta_ply.stat().st_size > 0)
                exportaciones.append({"modelo": relativo, "ply": ruta_ply.name,
                                      "exportado": valido, "codigo": proceso.returncode,
                                      "stderr_final": proceso.stderr[-1000:]})
            except subprocess.TimeoutExpired:
                exportaciones.append({"modelo": relativo, "ply": ruta_ply.name,
                                      "exportado": False, "error": "tiempo_agotado"})
    if estado == "reconstruccion_dispersa" and not any(e["exportado"] for e in exportaciones):
        estado = "exportacion_incompleta"
    informe = {
        "motor": "COLMAP", "estado": estado, "modelos_dispersos": modelos,
        "pasos": registro, "exportaciones_ply": exportaciones, "usa_gpu": bool(usar_gpu),
        "advertencia": "Reconstrucción dispersa, escala arbitraria. Sin malla densa ni medidas certificadas.",
    }
    (destino / "informe_colmap.json").write_text(
        json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if estado != "reconstruccion_dispersa":
        raise RuntimeError("COLMAP no completó la reconstrucción/exportación; consultar informe_colmap.json")
    return informe


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("fotos_dir", type=Path)
    p.add_argument("--salida", type=Path, required=True)
    p.add_argument("--colmap", default="colmap")
    p.add_argument("--gpu", action="store_true")
    p.add_argument("--timeout", type=int, default=7200)
    args = p.parse_args()
    print(json.dumps(ejecutar_colmap(args.fotos_dir, args.salida,
                                    args.colmap, args.gpu, args.timeout),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
