import unittest
import numpy as np
from tools.fusion_prealineada import fusionar_prealineadas


class TestFusionPrealineada(unittest.TestCase):
    def setUp(self):
        self.base = np.array([[0., 0, 0], [1, 0, 0], [0, 2, 0],
                              [0, 0, 3], [1, 2, 3], [2, 1, 1]])
        self.segunda = self.base + [0.015, -0.012, 0.008]

    def test_fusion_sin_correspondencias_manuales(self):
        nube, informe = fusionar_prealineadas(
            [self.base, self.segunda], radio=0.1, umbral=0.02, voxel=0.0)
        np.testing.assert_allclose(nube[:len(self.base)], self.base, atol=1e-10)
        np.testing.assert_allclose(nube[len(self.base):], self.base, atol=1e-7)
        self.assertEqual(informe["emparejamientos"][0]["pares_reciprocos"], 6)

    def test_falla_si_desalineadas(self):
        with self.assertRaisesRegex(ValueError, "insuficientes"):
            fusionar_prealineadas([self.base, self.segunda + 10],
                                 radio=0.1, umbral=0.02)

    def test_falla_umbral(self):
        with self.assertRaises(ValueError):
            fusionar_prealineadas([self.base, self.segunda],
                                 radio=0.1, umbral=0)

    def test_falla_base_vacia(self):
        with self.assertRaises(ValueError):
            fusionar_prealineadas([[], self.segunda], radio=0.1, umbral=0.02)


if __name__ == "__main__":
    unittest.main()
