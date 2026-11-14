import unittest
import numpy as np
from tools.auditar_registro import auditar_registro


class TestAuditarRegistro(unittest.TestCase):
    def setUp(self):
        self.a = np.array([[0., 0, 0], [1, 0, 0], [0, 2, 0], [0, 0, 3]])
        self.identidad = {"escala": 1., "rotacion": np.eye(3).tolist(),
                          "traslacion": [0, 0, 0]}

    def test_identidad(self):
        r = auditar_registro(self.a, self.a, self.identidad, 0.01)
        self.assertEqual(r["estado"], "cobertura_suficiente")
        self.assertEqual(r["cobertura_bidireccional"], 1.)

    def test_traslacion_corregida(self):
        b = self.a + [0.2, 0, 0]
        tf = dict(self.identidad, traslacion=[0.2, 0, 0])
        self.assertEqual(auditar_registro(self.a, b, tf, 0.01)["cobertura_bidireccional"], 1.)

    def test_no_coinciden(self):
        r = auditar_registro(self.a, self.a + 100, self.identidad, 0.01)
        self.assertEqual(r["estado"], "cobertura_insuficiente")

    def test_transformacion_invalida(self):
        tf = dict(self.identidad, rotacion=(np.eye(3) * 2).tolist())
        with self.assertRaises(ValueError):
            auditar_registro(self.a, self.a, tf, 0.01)

    def test_umbral_invalido(self):
        with self.assertRaises(ValueError):
            auditar_registro(self.a, self.a, self.identidad, float("nan"))

    def test_nube_vacia(self):
        with self.assertRaises(ValueError):
            auditar_registro([], self.a, self.identidad, 0.1)


if __name__ == "__main__":
    unittest.main()
