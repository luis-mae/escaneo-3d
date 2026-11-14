import tempfile
import unittest
from pathlib import Path

import numpy as np
from tools.leer_ply import leer_ply_xyz
from tools.nube_dos_vistas import guardar_ply


class TestLeerPLY(unittest.TestCase):
    def test_roundtrip(self):
        puntos = np.array([[0., 1., 2.], [3., 4., 5.], [-1., 0., 8.]])
        with tempfile.TemporaryDirectory() as tmp:
            archivo = Path(tmp) / "nube.ply"
            guardar_ply(puntos, archivo)
            np.testing.assert_allclose(leer_ply_xyz(archivo), puntos)

    def test_limite_puntos(self):
        with tempfile.TemporaryDirectory() as tmp:
            archivo = Path(tmp) / "nube.ply"
            guardar_ply(np.ones((3, 3)), archivo)
            with self.assertRaisesRegex(ValueError, "límite"):
                leer_ply_xyz(archivo, max_puntos=2)

    def test_rechaza_no_finitos(self):
        with tempfile.TemporaryDirectory() as tmp:
            archivo = Path(tmp) / "nube.ply"
            guardar_ply(np.ones((3, 3)), archivo)
            archivo.write_text(archivo.read_text().replace("1 1 1", "nan 1 1", 1))
            with self.assertRaisesRegex(ValueError, "no finitas"):
                leer_ply_xyz(archivo)

    def test_rechaza_datos_extra(self):
        with tempfile.TemporaryDirectory() as tmp:
            archivo = Path(tmp) / "nube.ply"
            guardar_ply(np.ones((3, 3)), archivo)
            with archivo.open("a") as f:
                f.write("0 0 0\n")
            with self.assertRaisesRegex(ValueError, "adicional"):
                leer_ply_xyz(archivo)


if __name__ == "__main__":
    unittest.main()
