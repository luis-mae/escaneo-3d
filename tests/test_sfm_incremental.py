import unittest
from unittest.mock import patch

import numpy as np

from tools.sfm_incremental import reconstruir_tracks


class TestSfmIncremental(unittest.TestCase):
    def test_rechaza_calibracion(self):
        with self.assertRaisesRegex(ValueError, "Calibración"):
            reconstruir_tracks({"puntos_por_imagen": {}, "tracks": []}, 0, 640, 480)

    def test_rechaza_tracks_insuficientes(self):
        datos = {"puntos_por_imagen": {"a": [[0, 0]], "b": [[1, 1]]},
                 "tracks": [{"a": 0, "b": 0}]}
        with self.assertRaisesRegex(ValueError, "suficientes"):
            reconstruir_tracks(datos, 800, 640, 480)

    def test_rechaza_indices_invalidos(self):
        datos = {"puntos_por_imagen": {"a": [[0, 0]], "b": [[1, 1]]},
                 "tracks": [{"a": 2, "b": 0}]}
        with self.assertRaisesRegex(ValueError, "fuera de rango"):
            reconstruir_tracks(datos, 800, 640, 480)

    def test_geometria_sintetica_dos_camaras(self):
        rng = np.random.default_rng(17)
        xyz = np.column_stack((rng.uniform(-2, 2, 100),
                               rng.uniform(-1, 1, 100),
                               rng.uniform(5, 10, 100)))
        K = np.array([[800., 0, 320], [0, 800., 240], [0, 0, 1.]])
        a = (K @ xyz.T).T
        b = (K @ (xyz + np.array([-0.8, 0., 0.])).T).T
        a = (a[:, :2] / a[:, 2:]).tolist()
        b = (b[:, :2] / b[:, 2:]).tolist()
        datos = {"puntos_por_imagen": {"a": a, "b": b},
                 "tracks": [{"a": i, "b": i} for i in range(100)]}
        resultado = reconstruir_tracks(datos, 800, 640, 480)
        self.assertEqual(resultado["estado"], "sfm_incremental_experimental")
        self.assertGreaterEqual(resultado["puntos_3d"], 12)
        self.assertEqual(len(resultado["camaras"]), 2)
        self.assertEqual(resultado["escala"], "arbitraria")


if __name__ == "__main__":
    unittest.main()
