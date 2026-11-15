"""Comprueba los reintentos del mallado antes del respaldo convexo."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np

from tools.colmap_a_malla import nube_colmap_a_malla


class ReintentosMallaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.puntos = np.array([[0., 0., 0.], [1., 0., 0.],
                                [0., 1., 0.], [0., 0., 1.]])
        self.caras = np.array([[0, 2, 1], [0, 1, 3],
                               [0, 3, 2], [1, 2, 3]])

    def test_reintenta_antes_de_usar_respaldo(self):
        def mallar(puntos, alpha):
            if alpha < 2:
                raise ValueError("alpha insuficiente")
            return self.puntos, self.caras, {"vertices": 4, "caras": 4}
        with patch("tools.colmap_a_malla.leer_nube_colmap_ply", return_value=self.puntos), \
             patch("tools.colmap_a_malla.procesar", side_effect=mallar):
            reporte = nube_colmap_a_malla(self.base / "nube.ply",
                                           self.base / "salida.obj", alpha=1)
        self.assertEqual(reporte["metodo_superficie"], "alpha_shape")
        self.assertEqual(reporte["alpha_efectivo"], 2.0)
        self.assertEqual(len(reporte["intentos_alpha"]), 2)
        self.assertTrue((self.base / "salida.obj").exists())

    def test_limita_presupuesto_antes_de_leer(self):
        with patch("tools.colmap_a_malla.leer_nube_colmap_ply") as lector:
            with self.assertRaises(ValueError):
                nube_colmap_a_malla(self.base / "nube.ply",
                                   self.base / "salida.obj", alpha=1,
                                   max_puntos=200000)
            lector.assert_not_called()

    def test_rechaza_alpha_no_finito(self):
        with patch("tools.colmap_a_malla.leer_nube_colmap_ply", return_value=self.puntos):
            with self.assertRaises(ValueError):
                nube_colmap_a_malla(self.base / "nube.ply",
                                   self.base / "salida.obj", alpha=float("nan"))


if __name__ == "__main__":
    unittest.main()
