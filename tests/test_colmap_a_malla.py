import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from tools.leer_colmap_ply import leer_nube_colmap_ply
from tools.colmap_a_malla import nube_colmap_a_malla


class TestLectorColmap(unittest.TestCase):
    def test_binario_con_colores(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / "nube.ply"
            header = (b"ply\nformat binary_little_endian 1.0\n"
                      b"element vertex 4\nproperty float x\nproperty float y\n"
                      b"property float z\nproperty uchar red\nend_header\n")
            datos = b"".join(struct.pack("<fffB", float(i), 1., 2., 255)
                             for i in range(4))
            ruta.write_bytes(header + datos)
            puntos = leer_nube_colmap_ply(ruta)
            self.assertEqual(puntos.shape, (4, 3))
            self.assertEqual(puntos[3].tolist(), [3., 1., 2.])

    def test_truncado(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / "nube.ply"
            ruta.write_bytes(b"ply\nformat binary_little_endian 1.0\n"
                             b"element vertex 4\nproperty float x\n"
                             b"property float y\nproperty float z\nend_header\n")
            with self.assertRaises(ValueError):
                leer_nube_colmap_ply(ruta)

    def test_malla_obj(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            ruta = raiz / "nube.ply"
            ruta.write_text("ply\nformat ascii 1.0\nelement vertex 4\n"
                            "property float x\nproperty float y\n"
                            "property float z\nend_header\n"
                            "0 0 0\n1 0 0\n0 1 0\n0 0 1\n")
            salida = raiz / "malla.obj"
            with patch("tools.colmap_a_malla.procesar",
                       return_value=(np.array([[0, 0, 0], [1, 0, 0],
                                               [0, 1, 0], [0, 0, 1]]),
                                     np.array([[0, 1, 2]]), {"caras": 1})):
                informe = nube_colmap_a_malla(ruta, salida, alpha=2.0)
            self.assertEqual(informe["caras"], 1)
            self.assertTrue(salida.exists())
            self.assertTrue(salida.with_suffix(".informe.json").exists())


if __name__ == "__main__":
    unittest.main()
