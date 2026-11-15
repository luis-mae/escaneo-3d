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

    def test_login_rechaza_cuerpo_excesivo(self):
        respuesta = self.client.post("/api/sesion",
            content=json.dumps({"usuario": "operador-prueba", "clave": "x" * 5000}),
            headers={"Content-Type": "application/json"})
        self.assertEqual(respuesta.status_code, 413, respuesta.text)

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
