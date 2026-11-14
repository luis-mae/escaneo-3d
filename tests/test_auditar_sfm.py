import unittest

import numpy as np

from tools.auditar_sfm import auditar_sfm


class TestAuditarSfm(unittest.TestCase):
    def setUp(self):
        self.K = np.array([[800., 0., 320.], [0., 800., 240.], [0., 0., 1.]])
        self.X = [[0., 0., 5.], [1., 0., 5.]]
        self.camaras = {"a": (np.eye(3), np.zeros(3)),
                        "b": (np.eye(3), np.array([-1., 0., 0.]))}

    def test_reproyeccion_exacta(self):
        observaciones = []
        for X in self.X:
            tr = {}
            for nombre, (R, t) in self.camaras.items():
                q = self.K @ (R @ np.asarray(X) + t)
                tr[nombre] = q[:2] / q[2]
            observaciones.append(tr)
        informe = auditar_sfm(self.X, [0, 1], observaciones, self.camaras, self.K)
        self.assertEqual(informe["observaciones_evaluadas"], 4)
        self.assertAlmostEqual(informe["rms_reproyeccion_px"], 0, places=9)
        self.assertEqual(informe["fraccion_bajo_umbral"], 1.0)

    def test_rechaza_puntos_no_finitos(self):
        with self.assertRaisesRegex(ValueError, "Puntos"):
            auditar_sfm([[float("nan"), 0, 1]], [0], [{}], self.camaras, self.K)

    def test_rechaza_indices_inconsistentes(self):
        with self.assertRaisesRegex(ValueError, "inconsistentes"):
            auditar_sfm(self.X, [0], [{}, {}], self.camaras, self.K)

    def test_rechaza_umbral_invalido(self):
        with self.assertRaisesRegex(ValueError, "Umbral"):
            auditar_sfm(self.X, [0, 1], [{}, {}], self.camaras, self.K, umbral_px=0)


if __name__ == "__main__":
    unittest.main()
