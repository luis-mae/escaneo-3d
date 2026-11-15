"""Pruebas del filtro geométrico opcional sin COLMAP."""
import unittest
import numpy as np
from tools.colmap_a_malla import filtrar_atipicos


class FiltradoAtipicosTests(unittest.TestCase):
    def test_rechaza_punto_aislado(self):
        rng = np.random.default_rng(42)
        nube = rng.normal(0, 0.1, size=(150, 3))
        nube = np.vstack((nube, [100, 100, 100]))
        filtrada, informe = filtrar_atipicos(nube)
        self.assertLess(len(filtrada), len(nube))
        self.assertFalse(np.any(np.all(filtrada == [100, 100, 100], axis=1)))
        self.assertGreater(informe["puntos_descartados"], 0)

    def test_no_altera_nube_pequena(self):
        nube = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=float)
        salida, informe = filtrar_atipicos(nube)
        np.testing.assert_array_equal(salida, nube)
        self.assertEqual(informe["puntos_descartados"], 0)

    def test_rechaza_nan(self):
        with self.assertRaises(ValueError):
            filtrar_atipicos(np.array([[float("nan"), 0, 0]]))


if __name__ == "__main__":
    unittest.main()
