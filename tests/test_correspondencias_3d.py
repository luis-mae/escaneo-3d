import unittest

import numpy as np
from tools.correspondencias_3d import correspondencias_mutuas


class TestCorrespondencias3D(unittest.TestCase):
    def setUp(self):
        self.a = np.array([[0., 0, 0], [1, 0, 0], [0, 2, 0], [0, 0, 3]])
        self.b = self.a + [0.01, -0.01, 0.]

    def test_recupera_pares_prealineados(self):
        r = correspondencias_mutuas(self.a, self.b, 0.05)
        self.assertEqual(r["cantidad"], 4)
        self.assertEqual(r["indices_origen"], [0, 1, 2, 3])
        self.assertEqual(r["indices_destino"], [0, 1, 2, 3])

    def test_rechaza_desalineacion(self):
        with self.assertRaisesRegex(ValueError, "insuficientes"):
            correspondencias_mutuas(self.a, self.b + [10, 0, 0], 0.05)

    def test_rechaza_radio_invalido(self):
        for radio in (0, -1, float("nan"), float("inf")):
            with self.subTest(radio=radio), self.assertRaises(ValueError):
                correspondencias_mutuas(self.a, self.b, radio)

    def test_rechaza_nube_no_finita(self):
        a = self.a.copy()
        a[0, 0] = float("nan")
        with self.assertRaises(ValueError):
            correspondencias_mutuas(a, self.b, 0.05)

    def test_unicidad_reciproca(self):
        a = np.array([[0., 0, 0], [0.001, 0, 0], [1, 0, 0], [2, 0, 0]])
        b = np.array([[0., 0, 0], [1, 0, 0], [2, 0, 0]])
        r = correspondencias_mutuas(a, b, 0.1)
        self.assertEqual(r["cantidad"], 3)
        self.assertEqual(len(set(r["indices_destino"])), 3)


if __name__ == "__main__":
    unittest.main()
