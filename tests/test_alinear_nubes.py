import unittest
import numpy as np
from tools.alinear_nubes import estimar_similitud, transformar

class AlinearNubesTests(unittest.TestCase):
    def test_recupera_escala_rotacion_y_traslacion(self):
        a = np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1],[1,2,3]], dtype=float)
        rot = np.array([[0,-1,0],[1,0,0],[0,0,1]])
        b = 2.5 * a @ rot + [4,-3,8]
        ajuste = estimar_similitud(a,b)
        self.assertTrue(np.allclose(transformar(a, ajuste),b,atol=1e-8))
        self.assertLess(ajuste['error_rms'],1e-8)
    def test_rechaza_colineales(self):
        with self.assertRaises(ValueError):
            estimar_similitud([[0,0,0],[1,0,0],[2,0,0]],[[0,0,0],[1,0,0],[2,0,0]])
    def test_rechaza_pocos(self):
        with self.assertRaises(ValueError):
            estimar_similitud([[0,0,0]],[[1,0,0]])

if __name__ == '__main__':
    unittest.main()
