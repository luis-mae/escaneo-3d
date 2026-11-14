"""Adaptador experimental para ejecutar COLMAP instalado localmente.

COLMAP es una dependencia externa GPL; no se distribuye ni instala aquí.
Requiere ejecutable colmap disponible en PATH y fotografías locales.
"""
import argparse
import json
import shutil
import subprocess
import time
from pathlib import Path

from .proceso_controlado import ejecutar_comando


def _ply_con_vertices(ruta):
    """Verifica encabezado y cantidad de puntos sin cargar la nube completa."""
    try:
        with Path(ruta).open("rb") as fuente:
            if fuente.readline().strip() != b"ply":
                return False
            formato = fuente.readline().strip()
            if formato not in (b"format ascii 1.0", b"format binary_little_endian 1.0",
                               b"format binary_big_endian 1.0"):
                return False
            vertices = None
            for _ in range(256):
                linea = fuente.readline()
                if not linea or len(linea) > 8192:
                    return False
                if linea.strip() == b"end_header":
                    return vertices is not None and vertices >= 4 and fuente.read(1) != b""
                partes = linea.split()
                if len(partes) == 3 and partes[:2] == [b"element", b"vertex"]:
                    vertices = int(partes[2])
    except (OSError, ValueError):
        return False
    return False


def ejecutar_colmap(fotos_dir, salida, ejecutable="colmap", usar_gpu=False,
                    timeout_segundos=7200, cancel_event=None):
    fotos = Path(fotos_dir).resolve()
    destino = Path(salida).resolve()
    if not fotos.is_dir():
        raise ValueError("Se requiere carpeta con fotografías JPG/PNG")
    imagenes = [p for p in fotos.iterdir()
                if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}]
    if len(imagenes) < 3:
        raise ValueError("Se requieren al menos 3 fotografías JPG/PNG para reconstruir")
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
                               "--ImageReader.single_camera", "0",
                               "--SiftExtraction.use_gpu", str(int(usar_gpu))]),
        ("exhaustive_matcher", ["--database_path", str(base),
                                "--SiftMatching.use_gpu", str(int(usar_gpu))]),
        ("mapper", ["--database_path", str(base),
                    "--image_path", str(fotos), "--output_path", str(sparse)]),
    ]
    registro = []
    limite_global = time.monotonic() + timeout_segundos
    for nombre, opciones in pasos:
        comando = [binario, nombre, *opciones]
        inicio_paso = time.monotonic()
        restante = min(timeout_segundos, limite_global - time.monotonic())
        if restante <= 0:
            registro.append({"paso": nombre, "error": "presupuesto_total_agotado",
                             "duracion_segundos": round(time.monotonic() - inicio_paso, 3)})
            break
        try:
            proceso = ejecutar_comando(comando, restante, cancel_event=cancel_event)
            entrada = {"paso": nombre, "codigo": proceso.returncode,
                       "duracion_segundos": round(time.monotonic() - inicio_paso, 3),
                       "stdout_final": proceso.stdout[-3000:],
                       "stderr_final": proceso.stderr[-3000:]}
        except subprocess.TimeoutExpired:
            entrada = {"paso": nombre, "error": "presupuesto_total_o_timeout_agotado",
                       "duracion_segundos": round(time.monotonic() - inicio_paso, 3)}
        registro.append(entrada)
        if entrada.get("codigo") != 0:
            break
    # Algunos modelos COLMAP terminan con código distinto de cero aun habiendo
    # escrito una reconstrucción válida; no se considera éxito sin los tres pasos.
    modelos = sorted(str(p.relative_to(destino)) for p in sparse.iterdir()
                     if p.is_dir() and (p / "cameras.bin").is_file()
                     and (p / "images.bin").is_file() and (p / "points3D.bin").is_file()
                     and (p / "cameras.bin").stat().st_size > 0
                     and (p / "images.bin").stat().st_size > 0
                     and (p / "points3D.bin").stat().st_size > 0)
    estado = "reconstruccion_dispersa" if modelos and len(registro) == 3 and all(
        p.get("codigo") == 0 for p in registro) else "incompleto"
    exportaciones = []
    if estado == "reconstruccion_dispersa":
        for indice, relativo in enumerate(modelos):
            ruta_ply = destino / f"modelo_{indice:03d}.ply"
            inicio_exportacion = time.monotonic()
            restante = min(timeout_segundos, limite_global - time.monotonic())
            if restante <= 0:
                exportaciones.append({"modelo": relativo, "ply": ruta_ply.name,
                                      "exportado": False, "error": "presupuesto_total_agotado"})
                break
            try:
                proceso = ejecutar_comando(
                    [binario, "model_converter", "--input_path", str(destino / relativo),
                     "--output_path", str(ruta_ply), "--output_type", "PLY"],
                    restante, cancel_event=cancel_event)
                valido = (proceso.returncode == 0 and ruta_ply.is_file()
                          and ruta_ply.stat().st_size > 0 and _ply_con_vertices(ruta_ply))
                exportaciones.append({"modelo": relativo, "ply": ruta_ply.name,
                                      "exportado": valido, "codigo": proceso.returncode,
                                      "duracion_segundos": round(time.monotonic() - inicio_exportacion, 3),
                                      "stderr_final": proceso.stderr[-1000:]})
            except subprocess.TimeoutExpired:
                exportaciones.append({"modelo": relativo, "ply": ruta_ply.name,
                                      "exportado": False, "error": "tiempo_agotado",
                                      "duracion_segundos": round(time.monotonic() - inicio_exportacion, 3)})
    # No dejar PLY parciales que luego puedan confundirse con nubes utilizables.
    for exportacion in exportaciones:
        if not exportacion.get("exportado"):
            (destino / exportacion["ply"]).unlink(missing_ok=True)
    if estado == "reconstruccion_dispersa" and not any(e["exportado"] for e in exportaciones):
        estado = "exportacion_incompleta"
    informe = {
        "motor": "COLMAP", "estado": estado, "modelos_dispersos": modelos,
        "pasos": registro, "exportaciones_ply": exportaciones, "usa_gpu": bool(usar_gpu),
        "presupuesto_total_segundos": timeout_segundos,
        "advertencia": "Reconstrucción dispersa, escala arbitraria. Sin malla densa ni medidas certificadas.",
    }
    (destino / "informe_colmap.json").write_text(
        json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if estado != "reconstruccion_dispersa":
        fallidos = [p for p in registro if p.get("codigo") != 0]
        ultimo = fallidos[-1] if fallidos else {}
        detalle = (ultimo.get("stderr_final") or ultimo.get("stdout_final") or
                   ultimo.get("error") or "").strip().splitlines()
        mensaje = detalle[-1][:240] if detalle else "Sin detalle de COLMAP"
        raise RuntimeError(
            f"COLMAP no completó la reconstrucción ({estado}); "
            f"paso {ultimo.get('paso', 'exportación PLY')}: {mensaje}. "
            "Consultar informe_colmap.json")
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
