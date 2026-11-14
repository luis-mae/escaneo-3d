"""Importa un proyecto local existente a la cola experimental de workers.

No altera el estado de la API ni sus cuotas. Ejecutar únicamente con la API
detenida y después de comprobar que el proyecto pertenece al operador.
"""
import argparse
import json
import re
import shutil
import tempfile
from pathlib import Path

from PIL import Image

from tools.cola_persistente import ColaPersistente

ID = re.compile(r"^[a-f0-9]{32}$")
EXT = {".jpg", ".jpeg", ".png"}


def importar_proyecto(origen, base, identificador, propietario):
    if not ID.fullmatch(identificador):
        raise ValueError("ID inválido")
    if not propietario or not propietario.strip():
        raise ValueError("Propietario obligatorio")
    origen = Path(origen).resolve()
    base = Path(base).resolve()
    if origen == base or origen in base.parents or base in origen.parents:
        raise ValueError("Almacenamientos de origen y destino deben ser independientes")
    estado = origen / identificador / "estado.json"
    fotos = origen / identificador / "fotos"
    if estado.is_symlink() or fotos.is_symlink() or not estado.is_file() or not fotos.is_dir():
        raise ValueError("Proyecto local incompleto")
    registro = json.loads(estado.read_text(encoding="utf-8"))
    if registro.get("id") != identificador:
        raise ValueError("ID no coincide con estado")
    if registro.get("user_id") != propietario:
        raise PermissionError("El propietario no coincide o el proyecto es anónimo")
    if registro.get("estado") in ("en_cola", "procesando"):
        raise ValueError("No importar un proyecto activo")
    archivos = list(fotos.iterdir())
    if not 1 <= len(archivos) <= 100:
        raise ValueError("Cantidad de fotos inválida")
    if any(p.is_symlink() or not p.is_file() or p.suffix.lower() not in EXT for p in archivos):
        raise ValueError("Archivos no admitidos")
    destino = base / "entradas" / identificador / "fotos"
    if destino.parent.exists():
        raise FileExistsError("Proyecto ya importado")
    destino.parent.parent.mkdir(parents=True, exist_ok=True)
    cola = ColaPersistente(base / "cola.sqlite")
    if cola.consultar(identificador, propietario) is not None:
        raise FileExistsError("Trabajo ya registrado en la cola")
    temporal = Path(tempfile.mkdtemp(prefix=".import-", dir=destino.parent.parent))
    publicado = False
    try:
        carpeta = temporal / "fotos"
        carpeta.mkdir()
        for archivo in archivos:
            with Image.open(archivo) as imagen:
                imagen.verify()
            shutil.copy2(archivo, carpeta / archivo.name)
        temporal.rename(destino.parent)
        publicado = True
        if not cola.agregar(identificador, propietario):
            raise FileExistsError("Trabajo ya registrado en la cola")
    except BaseException:
        if publicado and destino.parent.exists():
            shutil.rmtree(destino.parent)
        if temporal.exists():
            shutil.rmtree(temporal)
        raise
    return identificador


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origen", type=Path, required=True)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--id", required=True)
    parser.add_argument("--propietario", required=True)
    args = parser.parse_args(argv)
    print(importar_proyecto(args.origen, args.base, args.id, args.propietario))


if __name__ == "__main__":
    main()
