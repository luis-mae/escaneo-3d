"""API de eliminación de fondo: validación y dependencia opcional."""
import io
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image
from tools.servidor_web import app


class QuitarFondoAPITests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_rechaza_tipo_invalido(self):
        r = self.client.post("/api/quitar-fondo", files={
            "foto": ("texto.txt", b"no es foto", "text/plain")
        })
        self.assertEqual(r.status_code, 415)

    def test_rechaza_imagen_danada(self):
        r = self.client.post("/api/quitar-fondo", files={
            "foto": ("rota.png", b"contenido invalido", "image/png")
        })
        self.assertEqual(r.status_code, 400)

    def test_devuelve_png_transparente_con_motor_simulado(self):
        foto = io.BytesIO()
        Image.new("RGB", (4, 4), (255, 255, 255)).save(foto, "PNG")
        salida = Image.new("RGBA", (4, 4), (255, 0, 0, 0))
        with patch.dict("sys.modules", {"rembg": type("FakeRembg", (), {
            "remove": staticmethod(lambda imagen, session=None: salida),
            "new_session": staticmethod(lambda nombre: object())
        })()}):
            r = self.client.post("/api/quitar-fondo", files={
                "foto": ("foto.png", foto.getvalue(), "image/png")
            })
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.headers["content-type"], "image/png")
        with Image.open(io.BytesIO(r.content)) as resultado:
            self.assertEqual(resultado.mode, "RGBA")
            self.assertEqual(resultado.getpixel((0, 0))[3], 0)


if __name__ == "__main__":
    unittest.main()
