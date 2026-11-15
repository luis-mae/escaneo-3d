"""Diagnóstico de entorno Windows para ejecutar el MVP sin repetir COLMAP."""
import argparse
import importlib.util
import json
import platform
import shutil
import sys
from pathlib import Path

from .verificar_sesion_mvp import verificar_sesion


def diagnosticar_entorno(sesion=None):
    modulos = ("numpy", "scipy", "PIL")
    dependencias = {m: importlib.util.find_spec(m) is not None for m in modulos}
    informe = {
        "python": sys.version.split()[0],
        "plataforma": platform.platform(),
        "dependencias": dependencias,
        "colmap_en_path": shutil.which("colmap"),
        "puede_procesar_ply": all(dependencias.values()),
        "sesion": None,
        "problemas": [],
    }
    if not informe["puede_procesar_ply"]:
        informe["problemas"].append("Instalar dependencias: python -m pip install -r requirements.txt")
    if sesion is not None:
        try:
            estado = verificar_sesion(Path(sesion))
            informe["sesion"] = {
                "ruta": estado["carpeta"],
                "ply_detectados": len(estado["nubes_validas_por_cabecera"]),
                "nube_elegida": estado["reutilizar_nube"],
                "clasificacion_nube": estado["clasificacion_nube"],
                "requiere_validacion_visual": True,
            }
            if not estado["reutilizar_nube"]:
                informe["problemas"].append(
                    "No hay PLY reutilizable; no ejecutar mallado sin localizar resultados de COLMAP"
                )
        except (OSError, ValueError) as exc:
            informe["problemas"].append(f"Sesión inaccesible: {exc}")
    informe["listo_para_reanudar"] = not informe["problemas"]
    return informe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sesion", type=Path)
    args = parser.parse_args()
    reporte = diagnosticar_entorno(args.sesion)
    print(json.dumps(reporte, ensure_ascii=False, indent=2))
    raise SystemExit(0 if reporte["listo_para_reanudar"] else 1)


if __name__ == "__main__":
    main()
