"""Pruebas de límites de API sin FastAPI ni servicios externos."""
import unittest
from unittest.mock import patch

from tools import limites_api


class LimitesApiTests(unittest.TestCase):
    def setUp(self):
        limites_api._BUCKETS.clear()

    def test_get_no_consume_cupo(self):
        for _ in range(100):
            self.assertEqual(limites_api.permitir("ip-a", "/api/proyectos", "GET", 100), (True, 0))
        self.assertEqual(limites_api.permitir("ip-a", "/api/proyectos", "POST", 100), (True, 0))

    def test_limite_de_subidas_por_ip(self):
        for _ in range(4):
            self.assertEqual(limites_api.permitir("ip-a", "/api/proyectos", "POST", 100), (True, 0))
        permitido, espera = limites_api.permitir("ip-a", "/api/proyectos", "POST", 100)
        self.assertFalse(permitido)
        self.assertGreater(espera, 0)
        self.assertTrue(limites_api.permitir("ip-b", "/api/proyectos", "POST", 100)[0])
        self.assertTrue(limites_api.permitir("ip-a", "/api/proyectos", "POST", 3701)[0])

    def test_login_tiene_limite_propio(self):
        for _ in range(5):
            self.assertTrue(limites_api.permitir("ip-a", "/api/sesion", "POST", 100)[0])
        permitido, espera = limites_api.permitir("ip-a", "/api/sesion", "POST", 100)
        self.assertFalse(permitido)
        self.assertGreaterEqual(espera, 899)
        self.assertTrue(limites_api.permitir("ip-a", "/api/proyectos", "POST", 100)[0])
        self.assertTrue(limites_api.permitir("ip-a", "/api/sesion", "POST", 1001)[0])

    def test_mutaciones_separadas_de_subidas(self):
        for _ in range(60):
            self.assertTrue(limites_api.permitir("ip-a", "/api/proyectos/abc/cancelar", "POST", 100)[0])
        self.assertFalse(limites_api.permitir("ip-a", "/api/proyectos/abc/cancelar", "POST", 100)[0])
        self.assertTrue(limites_api.permitir("ip-a", "/api/proyectos", "POST", 100)[0])


if __name__ == "__main__":
    unittest.main()
