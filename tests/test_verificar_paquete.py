import hashlib
import json
import zipfile

import pytest

from tools.verificar_paquete import verificar_paquete


def crear_paquete(ruta, nombre="nube.ply", datos=b"ply"):
    manifiesto = {
        "archivos": [{
            "archivo": nombre,
            "bytes": len(datos),
            "sha256": hashlib.sha256(datos).hexdigest(),
        }],
        "fotos_originales_incluidas": False,
    }
    with zipfile.ZipFile(ruta, "w") as paquete:
        paquete.writestr(nombre, datos)
        paquete.writestr("MANIFEST.json", json.dumps(manifiesto))
        paquete.writestr("LEEME.txt", "No incluye fotografías originales.")


def test_verifica_paquete_valido(tmp_path):
    ruta = tmp_path / "resultados.zip"
    crear_paquete(ruta)
    informe = verificar_paquete(ruta)
    assert informe == {
        "valido": True,
        "archivos_verificados": 1,
        "fotos_originales_incluidas": False,
    }


def test_detecta_archivo_alterado(tmp_path):
    ruta = tmp_path / "alterado.zip"
    crear_paquete(ruta)
    with zipfile.ZipFile(ruta, "a") as paquete:
        paquete.writestr("nube.ply", b"contenido alterado")
    with pytest.raises(ValueError, match="duplicados"):
        verificar_paquete(ruta)


def test_rechaza_ruta_traversal_en_manifest(tmp_path):
    ruta = tmp_path / "inseguro.zip"
    datos = b"secreto"
    manifiesto = {
        "archivos": [{
            "archivo": "../secreto.txt",
            "bytes": len(datos),
            "sha256": hashlib.sha256(datos).hexdigest(),
        }],
        "fotos_originales_incluidas": False,
    }
    with zipfile.ZipFile(ruta, "w") as paquete:
        paquete.writestr("../secreto.txt", datos)
        paquete.writestr("MANIFEST.json", json.dumps(manifiesto))
        paquete.writestr("LEEME.txt", "test")
    with pytest.raises(ValueError, match="Ruta insegura"):
        verificar_paquete(ruta)


def test_rechaza_imagenes_en_paquete(tmp_path):
    ruta = tmp_path / "con_foto.zip"
    crear_paquete(ruta, "foto.jpg", b"imagen")
    with pytest.raises(ValueError, match="archivos de imagen"):
        verificar_paquete(ruta)
