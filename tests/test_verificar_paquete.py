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
    datos = b"contenido alterado"
    manifiesto = {
        "archivos": [{
            "archivo": "nube.ply",
            "bytes": len(datos),
            "sha256": "0" * 64,
        }],
        "fotos_originales_incluidas": False,
    }
    with zipfile.ZipFile(ruta, "w") as paquete:
        paquete.writestr("nube.ply", datos)
        paquete.writestr("MANIFEST.json", json.dumps(manifiesto))
        paquete.writestr("LEEME.txt", "test")
    with pytest.raises(ValueError, match="SHA-256 incorrecto"):
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


@pytest.mark.parametrize("nombre", ["foto.jpg", "captura.webp", "original.heic", "scan.tiff"])
def test_rechaza_imagenes_en_paquete(tmp_path, nombre):
    ruta = tmp_path / "con_foto.zip"
    crear_paquete(ruta, nombre, b"imagen")
    with pytest.raises(ValueError, match="archivos de imagen"):
        verificar_paquete(ruta)


@pytest.mark.parametrize("nombre", ["..\\\\fuera.txt", "C:/fuera.txt", "/etc/passwd"])
def test_rechaza_rutas_no_portables_o_absolutas(tmp_path, nombre):
    ruta = tmp_path / "ruta_insegura.zip"
    datos = b"x"
    manifiesto = {
        "archivos": [{
            "archivo": nombre,
            "bytes": 1,
            "sha256": hashlib.sha256(datos).hexdigest(),
        }],
        "fotos_originales_incluidas": False,
    }
    with zipfile.ZipFile(ruta, "w") as paquete:
        paquete.writestr(nombre, datos)
        paquete.writestr("MANIFEST.json", json.dumps(manifiesto))
        paquete.writestr("LEEME.txt", "test")
    with pytest.raises(ValueError, match="Ruta insegura"):
        verificar_paquete(ruta)
