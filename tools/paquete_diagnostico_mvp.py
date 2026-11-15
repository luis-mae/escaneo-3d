"""Genera un ZIP de diagnóstico liviano para compartir sin subir fotografías.

Incluye estado del entorno, resumen de sesión y cabeceras de nubes PLY,
pero nunca imágenes, nubes completas, credenciales ni bases de datos.
"""
import argparse
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from .diagnosticar_entorno_mvp import diagnosticar_entorno


def generar_diagnostico(sesion, destino, max_cabeceras=5):
    sesion, destino = Path(sesion).resolve(), Path(destino).resolve()
    if not sesion.is_dir():
        raise ValueError("No existe la sesión")
    if destino.is_relative_to(sesion):
        raise ValueError("Guardar el ZIP fuera de la sesión original")
    if destino.exists():
        raise FileExistsError("El ZIP de diagnóstico ya existe")
    if destino.suffix.lower() != ".zip":
        raise ValueError("El destino debe ser un ZIP")
    if not 0 <= max_cabeceras <= 20:
        raise ValueError("Cantidad de cabeceras inválida")
    entorno = diagnosticar_entorno(sesion)
    # Quitar rutas absolutas: pueden contener nombres privados de usuario.
    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "python": entorno["python"],
        "plataforma": entorno["plataforma"],
        "dependencias": entorno["dependencias"],
        "colmap_disponible": bool(entorno["colmap_en_path"]),
        "puede_procesar_ply": entorno["puede_procesar_ply"],
        "problemas": [
            "Sesión inaccesible" if p.startswith("Sesión inaccesible:")
            else p for p in entorno["problemas"]
        ],
        "ply_detectados": (entorno["sesion"] or {}).get("ply_detectados", 0),
        "nube_elegida": (
            Path(entorno["sesion"]["nube_elegida"]).name
            if entorno["sesion"] and entorno["sesion"]["nube_elegida"] else None
        ),
    }
    # Leer solo las cabeceras; no almacenar coordenadas de puntos ni fotos.
    cabeceras = []
    if entorno["sesion"] and entorno["sesion"]["nube_elegida"]:
        nube = Path(entorno["sesion"]["nube_elegida"])
        if nube.is_file() and nube.resolve().is_relative_to(sesion):
            lineas = []
            with nube.open("rb") as archivo:
                for _ in range(80):
                    linea = archivo.readline(4096)
                    if not linea:
                        break
                    texto = linea.decode("ascii", errors="replace").strip()
                    if texto == "end_header":
                        lineas.append(texto)
                        break
                    # Mantener solo propiedades PLY conocidas, no comentarios arbitrarios.
                    if texto.startswith(("ply", "format ", "element ", "property ")):
                        lineas.append(texto[:200])
            cabeceras.append({"archivo": nube.name, "cabecera": lineas})
    destino.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destino, "x", compression=zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr("diagnostico.json", json.dumps(
            resumen, ensure_ascii=False, indent=2
        ))
        zipf.writestr("cabeceras_ply.json", json.dumps(
            cabeceras[:max_cabeceras], ensure_ascii=False, indent=2
        ))
        zipf.writestr("LEEME.txt",
            "Este ZIP no contiene fotos ni modelos completos. "
            "Sirve para diagnosticar la sesión, no para reconstruir el objeto.\n")
    return {"zip": str(destino), "ply_detectados": resumen["ply_detectados"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sesion", type=Path)
    parser.add_argument("--salida", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(generar_diagnostico(args.sesion, args.salida),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
