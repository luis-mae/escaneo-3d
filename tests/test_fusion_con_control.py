import unittest
import numpy as np
from tools.fusion_con_control import fusionar_con_control


class TestFusionConControl(unittest.TestCase):
    def setUp(self):
        self.base = np.array([[0., 0, 0], [1, 0, 0], [0, 2, 0],
                              [0, 0, 3], [1, 2, 3], [2, 1, 1]])

    def test_identidad(self):
        nube, informe = fusionar_con_control([self.base, self.base], 0.1)
        self.assertEqual(len(nube), 12)
        self.assertEqual(informe["nubes"], 2)

    def test_traslacion(self):
        nube, informe = fusionar_con_control([self.base, self.base + [0.02, 0, 0]], 0.1)
        np.testing.assert_allclose(nube[6:], self.base, atol=1e-8)
        self.assertEqual(informe["registros"][0]["registro"]["escala"], 1.)

    def test_voxel(self):
        nube, _ = fusionar_con_control([self.base, self.base], 0.1, voxel=0.01)
        self.assertEqual(len(nube), 6)

    def test_sin_solapamiento(self):
        with self.assertRaises(ValueError):
            fusionar_con_control([self.base, self.base + 100], 0.1)

    def test_voxel_con_coordenadas_grandes(self):
        desplazamiento = np.array([1e9, -1e9, 1e9])
        nube, informe = fusionar_con_control(
            [self.base + desplazamiento, self.base + desplazamiento],
            radio=0.1, voxel=0.01)
        self.assertEqual(len(nube), 6)
        self.assertEqual(informe["puntos_entrada"], 12)

    def test_voxel_extremadamente_pequeno(self):
        with self.assertRaisesRegex(ValueError, "Voxel demasiado pequeño"):
            fusionar_con_control([self.base, self.base], 0.1, voxel=1e-30)

    def test_voxel_invalido(self):
        with self.assertRaises(ValueError):
            fusionar_con_control([self.base, self.base], 0.1, voxel=-1)


if __name__ == "__main__":
    unittest.main()
