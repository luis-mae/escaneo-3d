import unittest
import numpy as np
from tools.registro_con_control import registrar_con_control


class TestRegistroConControl(unittest.TestCase):
    def setUp(self):
        self.a = np.array([[0., 0, 0], [1, 0, 0], [0, 1, 0],
                           [0, 0, 1], [1, 1, 1]], float)

    def test_aprueba_identidad(self):
        r = registrar_con_control(self.a, self.a, 0.1)
        self.assertTrue(r["aprobado_para_fusion_experimental"])

    def test_rechaza_umbral_cobertura(self):
        with self.assertRaises(ValueError):
            registrar_con_control(self.a, self.a, 0.1, cobertura_minima=1.1)

    def test_rechaza_sin_solapamiento(self):
        with self.assertRaises(ValueError):
            registrar_con_control(self.a, self.a + 100, 0.1)
