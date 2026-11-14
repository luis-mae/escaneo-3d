"""Verifica integridad de exportaciones PLY/JSON de fusión controlada."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest()


def verificar_exportacion(carpeta):
    carpeta = Path(carpeta)
    ply = carpeta / "fusion_controlada.ply"
    informe = carpeta / "informe_controlado.json"
    if not ply.is_file() or not informe.is_file():
        raise ValueError("Faltan archivos PLY o informe JSON")
    datos = json.loads(informe.read_text(encoding="utf-8"))
    if not isinstance(datos, dict) or datos.get("estado") != "fusion_rigida_controlada_experimental":
        raise ValueError("Informe no corresponde a una fusión controlada")
    total = datos.get("puntos_salida")
    if type(total) is not int or total < 0:
        raise ValueError("Cantidad de puntos inválida en informe")
    with ply.open("r", encoding="ascii") as archivo:
        if archivo.readline().strip() != "ply":
            raise ValueError("Cabecera PLY inválida")
        if archivo.readline().strip() != "format ascii 1.0":
            raise ValueError("Formato PLY no admitido")
        vertices = None
        propiedades = []
        for _ in range(128):
            linea = archivo.readline()
            if not linea:
                raise ValueError("Cabecera PLY truncada")
            if linea.startswith("element ") and not linea.startswith("element vertex "):
                raise ValueError("Elemento PLY no admitido")
            if linea.startswith("element vertex "):
                if vertices is not None:
                    raise ValueError("Cabecera PLY duplicada")
                vertices = int(linea.split()[-1])
            if linea.startswith("property "):
                propiedades.append(linea.strip())
            if linea.strip() == "end_header":
                break
        else:
            raise ValueError("Cabecera PLY demasiado extensa")
        if propiedades != ["property float x", "property float y", "property float z"]:
            raise ValueError("Propiedades PLY no coinciden con el formato exportado")
        if vertices != total:
            raise ValueError("Cantidad de vértices PLY no coincide con informe")
        cantidad = 0
        for linea in archivo:
            if not linea.strip():
                raise ValueError("Fila vacía en PLY")
            campos = linea.split()
            if len(campos) != 3:
                raise ValueError("Fila de coordenadas PLY inválida")
            if not all(math.isfinite(float(c)) for c in campos):
                raise ValueError("Coordenadas PLY no finitas")
            cantidad += 1
        if cantidad != total:
            raise ValueError("Datos PLY truncados o adicionales")
    manifiesto = carpeta / "manifiesto_sha256.json"
    if manifiesto.exists():
        huellas = json.loads(manifiesto.read_text(encoding="utf-8"))
        esperado = {ply.name: sha256(ply), informe.name: sha256(informe)}
        if (not isinstance(huellas, dict) or huellas.get("algoritmo") != "sha256"
                or huellas.get("archivos") != esperado):
            raise ValueError("Manifiesto SHA256 no coincide con los archivos exportados")
    return {"estado": "estructura_consistente", "vertices": total,
            "sha256_ply": sha256(ply), "sha256_informe": sha256(informe),
            "advertencia": "Valida integridad estructural, no exactitud geométrica ni métrica."}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("carpeta", type=Path)
    args = p.parse_args()
    print(json.dumps(verificar_exportacion(args.carpeta), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
