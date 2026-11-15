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
    for archivo in encontrados:
        # No seguir enlaces que escapen de la sesión original.
        if not archivo.resolve().is_relative_to(raiz):
            continue
        cantidad = _cantidad_vertices_ply(archivo)
        if cantidad >= 4 and archivo.stat().st_size > 100:
            nubes.append({"archivo": str(archivo), "puntos_declarados": cantidad})
        if len(nubes) >= 200:
            break
    # Preferir nubes COLMAP frente a PLY de mallas exportadas o resultados
    # antiguos de la propia aplicación. Un PLY de malla no es una nube SfM.
    def prioridad(item):
        ruta = Path(item["archivo"])
        nombre = ruta.name.lower()
        partes = {p.lower() for p in ruta.parts}
        es_exportacion = bool(partes & {"exportados", "exports", "modelo_3d"})
        es_colmap = nombre.startswith("modelo_") or nombre == "fused.ply"
        return (
            not es_exportacion,
            nombre == "fused.ply" and not es_exportacion,
            es_colmap and not es_exportacion,
            item["puntos_declarados"],
        )
    nubes.sort(key=prioridad, reverse=True)
    nubes_elegibles = [
        n for n in nubes
        if not ({p.lower() for p in Path(n["archivo"]).parts}
                & {"exportados", "exports", "modelo_3d"})
    ]
    # Un archivo arbitrario puede contener una malla y no una nube de COLMAP.
    # En ese caso mostrarlo en diagnóstico, pero no procesarlo automáticamente.
    nubes_colmap = [
        n for n in nubes_elegibles
        if Path(n["archivo"]).name.lower() == "fused.ply"
        or Path(n["archivo"]).name.lower().startswith("modelo_")
    ]
    obj = sorted(str(p) for p in raiz.rglob("*.obj") if p.is_file())[:100]
    stl = sorted(str(p) for p in raiz.rglob("*.stl") if p.is_file())[:100]
    informes = sorted(str(p) for p in raiz.rglob("informe_colmap.json"))[:20]
    nube_elegida = nubes_colmap[0]["archivo"] if nubes_colmap else None
    es_densa = bool(nube_elegida and Path(nube_elegida).name.lower() == "fused.ply")
    decision = ("sin_nube" if not nube_elegida else
                "densa_por_nombre_sin_validar" if es_densa else
                "dispersa_o_desconocida_no_validada")
    return {
        "clasificacion_nube": decision,
        "nubes_colmap_candidatas": len(nubes_colmap),
        "requiere_validacion_visual": True,
        "carpeta": str(raiz), "nubes_validas_por_cabecera": nubes,
        "archivos_obj": obj, "archivos_stl": stl,
        "informes_colmap": informes,
        "reutilizar_nube": nube_elegida,
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
