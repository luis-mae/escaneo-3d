import base64
import hashlib
import hmac
import json
import os
import time
import unittest
from unittest.mock import patch

from tools.auth import TokenInvalido, validar_token


def _segmento(valor):
    return base64.urlsafe_b64encode(json.dumps(valor, separators=(",", ":")).encode()).decode().rstrip("=")


def _token(claims, secret="s" * 40, alg="HS256"):
    head = _segmento({"alg": alg, "typ": "JWT"})
    body = _segmento(claims)
    firma = base64.urlsafe_b64encode(
        hmac.new(secret.encode(), (head + "." + body).encode(), hashlib.sha256).digest()
    ).decode().rstrip("=")
    return "Bearer " + head + "." + body + "." + firma


class TestAuthJWT(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            "ESCANEO3D_JWT_SECRET": "s" * 40,
            "ESCANEO3D_JWT_ISSUER": "https://identity.example",
            "ESCANEO3D_JWT_AUDIENCE": "escaneo3d-api",
        })
        self.env.start()
        self.claims = {
            "sub": "usuario-123",
            "iss": "https://identity.example",
            "aud": "escaneo3d-api",
            "exp": int(time.time()) + 600,
        }

    def tearDown(self):
        self.env.stop()

    def test_token_valido_devuelve_subject(self):
        self.assertEqual(validar_token(_token(self.claims)), "usuario-123")

    def test_rechaza_token_vencido(self):
        claims = dict(self.claims, exp=int(time.time()) - 1)
        with self.assertRaises(TokenInvalido):
            validar_token(_token(claims))

    def test_rechaza_audiencia_incorrecta(self):
        claims = dict(self.claims, aud="otra-api")
        with self.assertRaises(TokenInvalido):
            validar_token(_token(claims))

    def test_rechaza_algoritmo_none(self):
        with self.assertRaises(TokenInvalido):
            validar_token(_token(self.claims, alg="none"))

    def test_rechaza_firma_alterada(self):
        token = _token(self.claims)
        with self.assertRaises(TokenInvalido):
            validar_token(token[:-2] + "xx")

    def test_exige_secreto_largo(self):
        with patch.dict(os.environ, {"ESCANEO3D_JWT_SECRET": "short"}):
            with self.assertRaises(RuntimeError):
                validar_token(_token(self.claims))


if __name__ == "__main__":
    unittest.main()
