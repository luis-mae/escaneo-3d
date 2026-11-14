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

    def test_orienta_caras_vecinas_con_adjacencia_compartida(self):
        vertices = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]
        ], dtype=float)
        caras = np.array([[0, 1, 2], [0, 3, 2]])
        _, reparadas, informe = reparar_malla(vertices, caras, cerrar_triangulos=False)
        sentidos = []
        for cara in reparadas:
            for a, b in ((cara[0], cara[1]), (cara[1], cara[2]), (cara[2], cara[0])):
                if {int(a), int(b)} == {0, 2}:
                    sentidos.append((int(a), int(b)))
        self.assertEqual(len(sentidos), 2)
        self.assertEqual(set(sentidos), {(0, 2), (2, 0)})
        self.assertEqual(informe["conflictos_orientacion"], 0)

    def test_cierra_agujero_triangular_tetraedro(self):
        v = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=float)
        f = np.array([[0, 2, 1], [0, 1, 3], [0, 3, 2]])
        _, caras, informe = reparar_malla(v, f)
        self.assertEqual(len(caras), 4)
        self.assertEqual(informe["caras_agregadas"], 1)
        self.assertTrue(informe["malla_cerrada_por_aristas"])
        sentidos = {}
        for cara in caras:
            for a, b in ((cara[0], cara[1]), (cara[1], cara[2]), (cara[2], cara[0])):
                sentidos.setdefault(tuple(sorted((int(a), int(b)))), []).append((int(a), int(b)))
        for pares in sentidos.values():
            self.assertEqual(len(pares), 2)
            self.assertEqual(pares[0], tuple(reversed(pares[1])))

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
