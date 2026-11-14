"""Pruebas sin red ni COLMAP para la comprobación de despliegue."""
import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import urlsplit

from tools.verificar_mvp import comprobar


class Respuesta:
    status = 200

    def __init__(self, contenido):
        self.contenido = contenido

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, _limite):
        return self.contenido


class VerificarMvpTest(unittest.TestCase):
    def test_rechaza_destinos_no_locales_y_credenciales(self):
        for url in ("https://example.com:8000", "http://example.com:8000",
                    "http://127.0.0.1:8000@evil.example:8000",
                    "http://localhost:8000/otra-ruta",
                    "http://localhost:8000?x=1", "http://localhost",
                    "http://user:pass@localhost:8000"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                comprobar(url)

    def test_endpoints_correctos(self):
        def abrir(url, timeout=10):
            ruta = urlsplit(url).path
            if ruta.endswith(("/00000000000000000000000000000000", "/id_invalido")):
                raise HTTPError(url, 404, "Not found", {},
                                io.BytesIO(b'{"detail":"Proyecto no encontrado"}'))
            contenidos = {
                "/api/salud": json.dumps({"colmap_detectado": True,
                                           "reconstruccion_densa": "disponible_sujeta_a_GPU_y_recursos",
                                           "trabajos_en_cola": 0, "limite_trabajos": 3}).encode(),
                "/": b"ESCANEO 3D app.js styles.css",
                "/app.js": b"const MAX_FOTOS = 100;",
                "/styles.css": b"body {}",
                "/sw.js": b"escaneo3d-shell-v8",
                "/manifest.webmanifest": json.dumps({"name":"ESCANEO 3D"}).encode(),
                "/api/proyectos": b'{"proyectos":[]}',
            }
            return Respuesta(contenidos[ruta])

        with patch("tools.verificar_mvp.urlopen", side_effect=abrir):
            resultados = comprobar("http://localhost:8000")
        self.assertTrue(all(x["ok"] for x in resultados.values()))
        self.assertTrue(resultados["/api/salud"]["colmap_detectado"])

    def test_respuesta_salud_sin_capacidad_densa_es_invalida(self):
        def abrir(url, timeout=10):
            ruta = urlsplit(url).path
            if ruta.endswith(("/00000000000000000000000000000000", "/id_invalido")):
                raise HTTPError(url, 404, "Not found", {},
                                io.BytesIO(b'{"detail":"Proyecto no encontrado"}'))
            contenidos = {
                "/api/salud": b'{"colmap_detectado":true}',
                "/": b"ESCANEO 3D app.js styles.css",
                "/app.js": b"const MAX_FOTOS = 100;",
                "/styles.css": b"body {}",
                "/sw.js": b"escaneo3d-shell-v8",
                "/manifest.webmanifest": json.dumps({"name":"ESCANEO 3D"}).encode(),
                "/api/proyectos": b'{"proyectos":[]}',
            }
            return Respuesta(contenidos[ruta])

        with patch("tools.verificar_mvp.urlopen", side_effect=abrir):
            resultados = comprobar("http://localhost:8000")
        self.assertFalse(resultados["/api/salud"]["ok"])

    def test_biblioteca_invalida_es_detectada(self):
        def abrir(url, timeout=10):
            ruta = urlsplit(url).path
            if ruta.endswith(("/00000000000000000000000000000000", "/id_invalido")):
                raise HTTPError(url, 404, "Not found", {},
                                io.BytesIO(b'{"detail":"Proyecto no encontrado"}'))
            contenidos = {
                "/api/salud": b'{"colmap_detectado":true,"reconstruccion_densa":"no_disponible","trabajos_en_cola":0,"limite_trabajos":3}',
                "/": b"ESCANEO 3D app.js styles.css",
                "/app.js": b"const MAX_FOTOS = 100;",
                "/styles.css": b"body {}",
                "/sw.js": b"escaneo3d-shell-v8",
                "/manifest.webmanifest": json.dumps({"name":"ESCANEO 3D"}).encode(),
                "/api/proyectos": b'{"proyectos":"esto no es una lista"}',
            }
            return Respuesta(contenidos[ruta])

        with patch("tools.verificar_mvp.urlopen", side_effect=abrir):
            resultados = comprobar("http://localhost:8000")
        self.assertFalse(resultados["/api/proyectos"]["ok"])

    def test_404_incorrecto_no_pasa(self):
        def abrir(url, timeout=10):
            raise HTTPError(url, 404, "Not found", {}, io.BytesIO(b'{"detail":"Otro error"}'))

        with patch("tools.verificar_mvp.urlopen", side_effect=abrir):
            resultados = comprobar("http://localhost:8000")
        self.assertFalse(resultados["/api/proyectos/00000000000000000000000000000000"]["ok"])


if __name__ == "__main__":
    unittest.main()
