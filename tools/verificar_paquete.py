"""Verifica integridad SHA-256 y estructura de un paquete ZIP de Escaneo 3D."""
import argparse
import hashlib
import json
import zipfile
from pathlib import PurePosixPath


def verificar_paquete(ruta):
    with zipfile.ZipFile(ruta, "r") as paquete:
        nombres = paquete.namelist()
        if len(nombres) != len(set(nombres)):
            raise ValueError("El ZIP contiene nombres de archivo duplicados")
        if "MANIFEST.json" not in nombres or "LEEME.txt" not in nombres:
            raise ValueError("Falta el manifiesto o el archivo LEEME")
        manifiesto = json.loads(paquete.read("MANIFEST.json"))
        if manifiesto.get("fotos_originales_incluidas") is not False:
            raise ValueError("El manifiesto no confirma la exclusión de fotos originales")
        entradas = manifiesto.get("archivos")
        if not isinstance(entradas, list) or not entradas:
            raise ValueError("El manifiesto no contiene archivos")
        esperados = set()
        for entrada in entradas:
            nombre = entrada.get("archivo")
            ruta_relativa = PurePosixPath(nombre or "")
            if (not nombre or ruta_relativa.is_absolute()
                    or ".." in ruta_relativa.parts or nombre in ("MANIFEST.json", "LEEME.txt")):
                raise ValueError("Ruta insegura o reservada en el manifiesto")
            if nombre in esperados:
                raise ValueError("Archivo duplicado en el manifiesto")
            esperados.add(nombre)
            if nombre not in nombres:
                raise ValueError("Falta un archivo declarado en el manifiesto: " + nombre)
            datos = paquete.read(nombre)
            if len(datos) != entrada.get("bytes"):
                raise ValueError("Tamaño incorrecto: " + nombre)
            digest = hashlib.sha256(datos).hexdigest()
            if digest != entrada.get("sha256"):
                raise ValueError("SHA-256 incorrecto: " + nombre)
        reales = set(nombres) - {"MANIFEST.json", "LEEME.txt"}
        if reales != esperados:
            raise ValueError("El ZIP contiene archivos no declarados en el manifiesto")
        if "original.jpg" in nombres or any(
            PurePosixPath(n).suffix.lower() in (".jpg", ".jpeg", ".png", ".heic")
            for n in nombres if n not in ("MANIFEST.json", "LEEME.txt")
        ):
            raise ValueError("El ZIP contiene archivos de imagen; revisar privacidad")
        return {"valido": True, "archivos_verificados": len(entradas),
                "fotos_originales_incluidas": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paquete")
    args = parser.parse_args()
    print(json.dumps(verificar_paquete(args.paquete), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
