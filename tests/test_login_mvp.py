"""Pruebas de emisión y validación de sesión privada sin red ni COLMAP."""
import hashlib
import os
import unittest
from unittest.mock import patch

from tools.auth import TokenInvalido, validar_token
from tools.login_mvp import comprobar_clave, emitir_token


class LoginMvpTests(unittest.TestCase):
    def setUp(self):
        self.salt = bytes.fromhex("00112233445566778899aabbccddeeff")
        self.password = "contraseña de prueba muy larga"
        digest = hashlib.pbkdf2_hmac("sha256", self.password.encode(), self.salt, 600000).hex()
        self.config = patch.dict(os.environ, {
            "ESCANEO3D_MVP_PASSWORD_HASH": "pbkdf2_sha256$600000$" + self.salt.hex() + "$" + digest,
            "ESCANEO3D_JWT_SECRET": "x" * 48,
            "ESCANEO3D_JWT_ISSUER": "escaneo3d-identidad",
            "ESCANEO3D_JWT_AUDIENCE": "escaneo3d-api",
        })
        self.config.start()

    def tearDown(self):
        self.config.stop()

    def test_login_y_token_valido(self):
        self.assertTrue(comprobar_clave(self.password))
        self.assertFalse(comprobar_clave("contraseña incorrecta"))
        token = emitir_token("operador")
        self.assertEqual(validar_token("Bearer " + token), "operador")

    def test_token_manipulado_rechazado(self):
        token = emitir_token("operador")
        partes = token.split(".")
        partes[2] = ("A" if partes[2][0] != "A" else "B") + partes[2][1:]
        with self.assertRaises(TokenInvalido):
            validar_token("Bearer " + ".".join(partes))

    def test_hash_mal_formado(self):
        with patch.dict(os.environ, {"ESCANEO3D_MVP_PASSWORD_HASH": "no-es-un-hash"}):
            self.assertFalse(comprobar_clave(self.password))


if __name__ == "__main__":
    unittest.main()
