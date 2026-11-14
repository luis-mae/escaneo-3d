import unittest

from tools.estimador_costos import estimar


class EstimadorCostosTest(unittest.TestCase):
    def test_suma_componentes(self):
        r = estimar(3600, 0.5, 2, 0.1, 3, 0.2)
        self.assertAlmostEqual(r["total_estimado"], 1.3)

    def test_rechaza_negativos_nan_e_inf(self):
        for valor in (-1, float("nan"), float("inf")):
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError):
                    estimar(valor, 1)

    def test_sin_consumo(self):
        self.assertEqual(estimar(0, 0)["total_estimado"], 0)


if __name__ == "__main__":
    unittest.main()
