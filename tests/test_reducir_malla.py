import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from reducir_malla import reducir


class ReducirMallaTest(unittest.TestCase):
    def test_sin_reduccion_en_celdas_distintas(self):
        caras = [((0., 0., 0.), (2., 0., 0.), (0., 2., 0.))]
        salida, datos = reducir(caras, 0.1)
        self.assertEqual(len(salida), 1)
        self.assertEqual(datos['triangulos_originales'], 1)

    def test_colapsa_triangulo_pequeno(self):
        caras = [((0., 0., 0.), (.01, 0., 0.), (0., .01, 0.)),
                 ((0., 0., 0.), (2., 0., 0.), (0., 2., 0.))]
        salida, _ = reducir(caras, .1)
        self.assertEqual(len(salida), 1)

    def test_parametros_invalidos(self):
        for valor in (0, -1, math.inf, math.nan):
            with self.assertRaises(ValueError):
                reducir([], valor)

    def test_no_finitos(self):
        with self.assertRaises(ValueError):
            reducir([((0,0,0),(1,0,0),(0,math.nan,0))], .1)


if __name__ == '__main__':
    unittest.main()
