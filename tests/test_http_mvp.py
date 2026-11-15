"""Prueba HTTP real del flujo privado, sin ejecutar COLMAP."""
import hashlib
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient


class FlujoHttpMvp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        sal = bytes.fromhex("00112233445566778899aabbccddeeff")
        cls.password = "clave de prueba del servidor"
        clave = hashlib.pbkdf2_hmac("sha256", cls.password.encode(), sal, 600000).hex()
        cls.env = patch.dict(os.environ, {
            "ESCANEO3D_ENV": "production",
            "ESCANEO3D_AUTH_REQUIRED": "1",
            "ESCANEO3D_DATA": cls.tmp.name,
            "ESCANEO3D_BILLING_DB": os.path.join(cls.tmp.name, "cuotas.sqlite3"),
            "ESCANEO3D_MVP_USER": "operador-prueba",
            "ESCANEO3D_MVP_PASSWORD_HASH": f"pbkdf2_sha256$600000${sal.hex()}${clave}",
            "ESCANEO3D_JWT_SECRET": "secret-for-test-only-" + "x" * 48,
            "ESCANEO3D_JWT_ISSUER": "escaneo3d-identidad",
            "ESCANEO3D_JWT_AUDIENCE": "escaneo3d-api",
        })
        cls.env.start()
        from tools.servidor_web import app
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        cls.env.stop()
        cls.tmp.cleanup()

    def test_login_rechaza_usuario_excesivo(self):
        respuesta = self.client.post("/api/sesion", json={
            "usuario": "a" * 201, "clave": self.password})
        self.assertEqual(respuesta.status_code, 400, respuesta.text)

    def test_login_rechaza_cuerpo_excesivo(self):
        respuesta = self.client.post("/api/sesion",
            content=json.dumps({"usuario": "operador-prueba", "clave": "x" * 5000}),
            headers={"Content-Type": "application/json"})
        self.assertEqual(respuesta.status_code, 413, respuesta.text)

    def test_carga_invalida_no_deja_proyecto_fantasma(self):
        from tools import servidor_web
        token = servidor_web.emitir_token("operador-prueba")
        headers = {"Authorization": "Bearer " + token}
        with patch("tools.servidor_web.shutil.which", return_value="/usr/bin/colmap"):
            respuesta = self.client.post("/api/proyectos", headers=headers,
                data={"nombre": "Prueba de foto inválida"},
                files=[("fotos", (f"foto{i}.jpg", b"no es una imagen", "image/jpeg"))
                       for i in range(3)])
        self.assertEqual(respuesta.status_code, 400, respuesta.text)
        listado = self.client.get("/api/proyectos", headers=headers)
        self.assertEqual(listado.status_code, 200, listado.text)
        self.assertFalse(any(p["nombre"] == "Prueba de foto inválida"
                             for p in listado.json()["proyectos"]))

    def test_carga_valida_inicia_pipeline_y_persiste_estado(self):
        import io
        import time
        from PIL import Image
        from tools import servidor_web

        imagen = io.BytesIO()
        Image.new("RGB", (64, 64), color=(120, 100, 80)).save(imagen, "JPEG")
        fotos = [("fotos", (f"foto{i}.jpg", imagen.getvalue(), "image/jpeg"))
                 for i in range(3)]
        token = servidor_web.emitir_token("operador-prueba")
        headers = {"Authorization": "Bearer " + token}
        with patch("tools.servidor_web.shutil.which", return_value="/usr/bin/colmap"), \
             patch("tools.servidor_web.pipeline_colmap",
                   side_effect=RuntimeError("fallo simulado del motor")) as motor:
            respuesta = self.client.post("/api/proyectos", headers=headers,
                data={"nombre": "Integracion carga real"}, files=fotos)
            self.assertEqual(respuesta.status_code, 202, respuesta.text)
            identificador = respuesta.json()["id"]
            for _ in range(100):
                estado = self.client.get("/api/proyectos/" + identificador,
                                        headers=headers).json()
                if estado.get("estado") in ("error", "cancelado", "completado"):
                    break
                time.sleep(0.02)
        self.assertEqual(estado["estado"], "error", estado)
        motor.assert_called_once()
        self.assertTrue((servidor_web.RAIZ / identificador / "estado.json").is_file())
        self.assertEqual(len(list((servidor_web.RAIZ / identificador / "fotos").glob("*.jpg"))), 3)

    def test_colmap_incompleto_se_reporta_error_y_no_exito(self):
        import io
        import time
        from PIL import Image
        from tools import servidor_web

        imagen = io.BytesIO()
        Image.new("RGB", (64, 64), color=(120, 100, 80)).save(imagen, "JPEG")
        fotos = [("fotos", (f"foto{i}.jpg", imagen.getvalue(), "image/jpeg"))
                 for i in range(3)]
        token = servidor_web.emitir_token("operador-prueba")
        headers = {"Authorization": "Bearer " + token}
        informe = {"disperso": {"estado": "incompleto",
                               "pasos": [{"paso": "mapper", "codigo": 1,
                                          "stderr_final": "sin correspondencias"}]}}
        with patch("tools.servidor_web.shutil.which", return_value="/usr/bin/colmap"), \
             patch("tools.servidor_web.pipeline_colmap", return_value=informe):
            respuesta = self.client.post("/api/proyectos", headers=headers,
                data={"nombre": "COLMAP incompleto"}, files=fotos)
            self.assertEqual(respuesta.status_code, 202, respuesta.text)
            identificador = respuesta.json()["id"]
            for _ in range(100):
                estado = self.client.get("/api/proyectos/" + identificador,
                                        headers=headers).json()
                if estado.get("estado") in ("error", "cancelado", "completado"):
                    break
                time.sleep(0.02)
        self.assertEqual(estado["estado"], "error", estado)
        self.assertIn("COLMAP no completó", estado["error"])

    def test_login_y_acceso_a_proyectos(self):
        self.assertEqual(self.client.get("/api/proyectos").status_code, 401)
        fallido = self.client.post("/api/sesion", json={
            "usuario": "operador-prueba", "clave": "incorrecta"})
        self.assertEqual(fallido.status_code, 401)
        acceso = self.client.post("/api/sesion", json={
            "usuario": "operador-prueba", "clave": self.password})
        self.assertEqual(acceso.status_code, 200, acceso.text)
        token = acceso.json()["token"]
        listado = self.client.get("/api/proyectos",
                                  headers={"Authorization": "Bearer " + token})
        self.assertEqual(listado.status_code, 200, listado.text)
        self.assertEqual(self.client.get("/api/proyectos", headers={
            "Authorization": "Bearer " + token + "alterado"}).status_code, 401)
        self.assertEqual(self.client.get("/api/salud").status_code, 200)


if __name__ == "__main__":
    unittest.main()
