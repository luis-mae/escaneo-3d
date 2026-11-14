import tempfile
import unittest
from pathlib import Path

import numpy as np

from tools.reparar_malla import reparar_malla, reparar_obj


class TestRepararMalla(unittest.TestCase):
    def test_descarta_duplicados_y_degenerados(self):
        v = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=float)
        f = np.array([[0, 1, 2], [2, 1, 0], [0, 0, 1], [0, 2, 3]])
        _, caras, informe = reparar_malla(v, f, cerrar_triangulos=False)
        self.assertEqual(len(caras), 2)
        self.assertEqual(informe["caras_descartadas"], 2)

    def test_cierra_agujero_triangular_tetraedro(self):
        v = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=float)
        f = np.array([[0, 2, 1], [0, 1, 3], [0, 3, 2]])
        _, caras, informe = reparar_malla(v, f)
        self.assertEqual(len(caras), 4)
        self.assertEqual(informe["caras_agregadas"], 1)
        self.assertTrue(informe["malla_cerrada_por_aristas"])

    def test_obj_no_sobrescribe(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            entrada = raiz / "entrada.obj"
            entrada.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
            salida = raiz / "salida.obj"
            salida.write_text("original")
            with self.assertRaises(FileExistsError):
                reparar_obj(entrada, salida)
            self.assertEqual(salida.read_text(), "original")

    def test_obj_reparado_crea_informe(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            entrada = raiz / "entrada.obj"
            entrada.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 0 1\n"
                               "f 1 3 2\nf 1 2 4\nf 1 4 3\n")
            salida = raiz / "salida.obj"
            informe = reparar_obj(entrada, salida)
            self.assertEqual(informe["caras_agregadas"], 1)
            self.assertTrue(salida.is_file())
            self.assertTrue(salida.with_suffix(".informe.json").is_file())


if __name__ == "__main__":
    unittest.main()
