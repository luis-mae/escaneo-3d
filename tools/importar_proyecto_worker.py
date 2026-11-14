"""Importa un proyecto local existente a la cola experimental de workers.

No altera el estado de la API ni sus cuotas. Ejecutar únicamente con la API
detenida y después de comprobar que el proyecto pertenece al operador.
"""
import argparse
import hashlib
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
    if not isinstance(identificador, str) or not ID.fullmatch(identificador):
        raise ValueError("ID inválido")
    if not isinstance(propietario, str) or not propietario.strip():
        raise ValueError("Propietario obligatorio")
    origen = Path(origen).resolve()
    base = Path(base).resolve()
    if origen == base or origen in base.parents or base in origen.parents:
        raise ValueError("Almacenamientos de origen y destino deben ser independientes")
    proyecto = origen / identificador
    if proyecto.is_symlink() or not proyecto.is_dir():
        raise ValueError("Directorio de proyecto no confiable")
    estado = proyecto / "estado.json"
    fotos = proyecto / "fotos"
    if (estado.is_symlink() or fotos.is_symlink() or not estado.is_file() or
            not fotos.is_dir()):
        raise ValueError("Proyecto local incompleto")
    registro = json.loads(estado.read_text(encoding="utf-8"))
    if registro.get("id") != identificador:
        raise ValueError("ID no coincide con estado")
    if registro.get("user_id") != propietario:
        raise PermissionError("El propietario no coincide o el proyecto es anónimo")
    if registro.get("estado") not in ("completado", "error", "cancelado", "interrumpido"):
        raise ValueError("Estado de proyecto no admitido para importación")
    archivos = list(fotos.iterdir())
    if any(p.is_symlink() or not p.is_file() for p in archivos):
        raise ValueError("No se admiten enlaces ni carpetas en fotografías")
    if any(p.stat().st_size == 0 or p.stat().st_size > 20 * 1024 * 1024 for p in archivos):
        raise ValueError("Fotografía demasiado grande")
    if sum(p.stat().st_size for p in archivos) > 500 * 1024 * 1024:
        raise ValueError("Tamaño total de fotografías excedido")
    if not 3 <= len(archivos) <= 100:
        raise ValueError("Cantidad de fotos inválida")
    if any(p.suffix.lower() not in EXT for p in archivos):
        raise ValueError("Archivos no admitidos")
    destino = base / "entradas" / identificador / "fotos"
    if destino.parent.exists():
        raise FileExistsError("Proyecto ya importado")
    destino.parent.parent.mkdir(parents=True, exist_ok=True)
    if (destino.parent.parent.is_symlink() or
            not destino.parent.parent.resolve().is_relative_to(base)):
        raise ValueError("Directorio de entradas no confiable")
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
            destino_foto = carpeta / archivo.name
            with archivo.open("rb") as entrada, destino_foto.open("xb") as salida:
                shutil.copyfileobj(entrada, salida)
            with Image.open(destino_foto) as imagen:
                imagen.verify()
            def digest(ruta):
                h = hashlib.sha256()
                with ruta.open("rb") as entrada:
                    for bloque in iter(lambda: entrada.read(1024 * 1024), b""):
                        h.update(bloque)
                return h.digest()
            if digest(archivo) != digest(destino_foto):
                raise IOError("La fotografía cambió durante la importación")
        # Renombrar sin reemplazar una carpeta creada por otro importador.
        destino.parent.mkdir(exist_ok=False)
        publicado = True
        carpeta.rename(destino)
        temporal.rmdir()
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
