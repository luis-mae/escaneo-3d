"""Fusiona dos o más PLY XYZ prealineados, con control de cobertura."""
import argparse
import json
from pathlib import Path

from .fusion_con_control import fusionar_con_control
from .leer_ply import leer_ply_xyz
from .nube_dos_vistas import guardar_ply
from .verificar_exportacion import verificar_exportacion


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("nubes", type=Path, nargs="+", help="Al menos dos archivos PLY XYZ")
    p.add_argument("--salida", type=Path, required=True)
    p.add_argument("--radio", type=float, required=True)
    p.add_argument("--cobertura-minima", type=float, default=0.6)
    p.add_argument("--voxel", type=float, default=0.)
    p.add_argument("--max-puntos", type=int, default=2_000_000)
    args = p.parse_args()
    if len(args.nubes) < 2:
        p.error("Se requieren al menos dos archivos PLY")
    if args.salida.exists() and any(args.salida.iterdir()):
        raise FileExistsError("La carpeta de salida debe estar vacía")
    nubes = [leer_ply_xyz(ruta, max_puntos=args.max_puntos) for ruta in args.nubes]
    fusion, informe = fusionar_con_control(nubes, args.radio, args.cobertura_minima, args.voxel)
    informe["fuentes"] = [str(p) for p in args.nubes]
    args.salida.mkdir(parents=True, exist_ok=True)
    guardar_ply(fusion, args.salida / "fusion_controlada.ply")
    (args.salida / "informe_controlado.json").write_text(
        json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    verificar_exportacion(args.salida)


if __name__ == "__main__":
    main()
