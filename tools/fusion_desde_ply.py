"""Fusiona dos o más PLY XYZ prealineados, con control de cobertura."""
import argparse
from pathlib import Path

from .fusion_con_control import fusionar_con_control, exportar_fusion
from .leer_ply import leer_ply_xyz


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("nubes", type=Path, nargs="+", help="Al menos dos archivos PLY XYZ")
    p.add_argument("--salida", type=Path, required=True)
    p.add_argument("--radio", type=float, required=True)
    p.add_argument("--cobertura-minima", type=float, default=0.6)
    p.add_argument("--voxel", type=float, default=0.)
    p.add_argument("--max-puntos", type=int, default=2_000_000)
    p.add_argument("--sobrescribir", action="store_true", help="Reemplazar exportación anterior")
    args = p.parse_args()
    if len(args.nubes) < 2:
        p.error("Se requieren al menos dos archivos PLY")
    if args.salida.exists() and not args.salida.is_dir():
        raise NotADirectoryError("La salida debe ser un directorio")
    nubes = [leer_ply_xyz(ruta, max_puntos=args.max_puntos) for ruta in args.nubes]
    fusion, informe = fusionar_con_control(nubes, args.radio, args.cobertura_minima, args.voxel)
    informe["fuentes"] = [str(p) for p in args.nubes]
    exportar_fusion(fusion, informe, args.salida, sobrescribir=args.sobrescribir)


if __name__ == "__main__":
    main()
