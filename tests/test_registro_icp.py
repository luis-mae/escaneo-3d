import unittest
import numpy as np
from tools.registro_icp import registrar_icp


class TestRegistroICP(unittest.TestCase):
    def setUp(self):
        self.a = np.array([[0., 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 1]], dtype=float)

    def test_traslacion_pequena(self):
        b = self.a + [0.04, -0.03, 0.02]
        r = registrar_icp(self.a, b, radio=0.2)
        np.testing.assert_allclose(r["traslacion"], [0.04, -0.03, 0.02], atol=1e-8)
        self.assertEqual(r["escala"], 1.0)
        self.assertEqual(r["auditoria_final"]["cobertura_bidireccional"], 1.0)

    def test_identidad(self):
        r = registrar_icp(self.a, self.a, radio=0.1)
        np.testing.assert_allclose(r["rotacion"], np.eye(3), atol=1e-8)
        self.assertLess(r["historial"][-1]["rmse"], 1e-8)
        self.assertEqual(r["auditoria_final"]["estado"], "cobertura_suficiente")

    def test_sin_solapamiento(self):
        with self.assertRaises(ValueError):
            registrar_icp(self.a, self.a + 100, radio=0.1)

    def test_radio_invalido(self):
        with self.assertRaises(ValueError):
            registrar_icp(self.a, self.a, radio=0)

    def test_iteraciones_invalidas(self):
        with self.assertRaises(ValueError):
            registrar_icp(self.a, self.a, radio=1, max_iter=0)
