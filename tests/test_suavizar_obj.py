import tempfile
import unittest
from pathlib import Path

import numpy as np

from tools.suavizar_obj import suavizar, suavizar_obj


class TestSuavizarObj(unittest.TestCase):
    def test_borde_permanece_inmovil(self):
        v = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.],
                      [0.3, 0.3, 0.5]])
        f = np.array([[0, 1, 3], [1, 2, 3], [2, 0, 3]])
        nuevo, _, informe = suavizar(v, f, iteraciones=2, intensidad=0.3)
        np.testing.assert_array_equal(nuevo[:3], v[:3])
        self.assertFalse(np.allclose(nuevo[3], v[3]))
        self.assertEqual(informe["vertices_protegidos"], 3)

    def test_rechaza_intensidad_invalida(self):
        v = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]])
        f = np.array([[0, 1, 2]])
        with self.assertRaises(ValueError):
            suavizar(v, f, intensidad=1.0)

    def test_crea_obj_e_informe(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            entrada = raiz / "original.obj"
            entrada.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
            salida = raiz / "suavizado.obj"
            informe = suavizar_obj(entrada, salida)
            self.assertEqual(informe["caras"], 1)
            self.assertTrue(salida.exists())
            self.assertTrue(salida.with_suffix(".informe.json").exists())


if __name__ == "__main__":
    unittest.main()
