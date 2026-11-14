import unittest
import numpy as np
from tools.triangular_puntos import triangular_puntos

class TriangularPuntosTests(unittest.TestCase):
    def setUp(self):
        self.K = np.array([[800., 0, 320], [0, 800, 240], [0, 0, 1]])
        self.xyz = np.array([[0, 0, 5], [1, .2, 6], [-.4, .5, 4], [.2, -.3, 7.]])
        self.t = np.array([-.5, 0, 0])
        self.a = self.project(self.xyz)
        self.b = self.project(self.xyz + self.t)
    def project(self, xyz):
        p = (self.K @ xyz.T).T
        return p[:, :2] / p[:, 2:]
    def test_triangula_escena_sintetica(self):
        result = triangular_puntos(self.a, self.b, self.K, np.eye(3), self.t)
        self.assertEqual(result['aceptados'], 4)
        np.testing.assert_allclose(result['puntos'], self.xyz, atol=1e-6)
    def test_rechaza_correspondencia_incoherente(self):
        b = self.b.copy()
        b[0] += [100, 90]
        result = triangular_puntos(self.a, b, self.K, np.eye(3), self.t)
        self.assertLess(result['aceptados'], 4)
    def test_rechaza_baseline_nula(self):
        with self.assertRaises(ValueError):
            triangular_puntos(self.a, self.b, self.K, np.eye(3), [0,0,0])
if __name__ == '__main__': unittest.main()
