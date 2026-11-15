"""Diagnóstico rápido de una sesión COLMAP existente, sin recalcular fotos.

Ejemplo Windows:
 python -m tools.verificar_sesion_mvp "A:\\escaneo3d" 
"""
import argparse
import json
from pathlib import Path

from .motor_colmap import _cantidad_vertices_ply


def verificar_sesion(carpeta):
    raiz = Path(carpeta).resolve()
    if not raiz.is_dir():
        raise ValueError("No existe la carpeta de la sesión")
    encontrados = sorted(
        (p for p in raiz.rglob("*.ply") if p.is_file()),
        key=lambda p: (p.name.lower() != "fused.ply", str(p)),
    )
    # Evitar recorridos arbitrariamente costosos y archivos no pertenecientes.
    nubes = []
    for archivo in encontrados[:200]:
        # No seguir enlaces que escapen de la sesión original.
        if not archivo.resolve().is_relative_to(raiz):
            continue
        cantidad = _cantidad_vertices_ply(archivo)
        if cantidad >= 4 and archivo.stat().st_size > 100:
            nubes.append({"archivo": str(archivo), "puntos_declarados": cantidad})
    nubes.sort(
        key=lambda item: (
            Path(item["archivo"]).name.lower() == "fused.ply",
            item["puntos_declarados"],
        ),
        reverse=True,
    )
    obj = sorted(str(p) for p in raiz.rglob("*.obj") if p.is_file())[:100]
    stl = sorted(str(p) for p in raiz.rglob("*.stl") if p.is_file())[:100]
    informes = sorted(str(p) for p in raiz.rglob("informe_colmap.json"))[:20]
    return {
        "carpeta": str(raiz), "nubes_validas_por_cabecera": nubes,
        "archivos_obj": obj, "archivos_stl": stl,
        "informes_colmap": informes,
        "reutilizar_nube": nubes[0]["archivo"] if nubes else None,
        "siguiente_paso": (
            "Usar python -m tools.procesar_nube_mvp <PLY> --salida <CARPETA_NUEVA>"
            if nubes else
            "No se detectó nube PLY; revisar salida de COLMAP antes de repetir fotografías."
        ),
        "advertencia": "La cabecera PLY no valida la geometría ni la escala.",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("carpeta", type=Path)
    args = p.parse_args()
    print(json.dumps(verificar_sesion(args.carpeta), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
