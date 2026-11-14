import tempfile
import unittest
from pathlib import Path

from tools.superficie_automatica import reconstruir_superficie_auto


class TestSuperficieAutomatica(unittest.TestCase):
    def test_tetraedro_genera_obj_e_informe(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            nube = raiz / "nube.ply"
            nube.write_text("ply\nformat ascii 1.0\nelement vertex 4\n"
                            "property float x\nproperty float y\n"
                            "property float z\nend_header\n"
                            "0 0 0\n1 0 0\n0 1 0\n0 0 1\n")
            salida = raiz / "modelo.obj"
            informe = reconstruir_superficie_auto(nube, salida)
            self.assertGreater(informe["caras"], 0)
            self.assertTrue(salida.exists())
            self.assertTrue(salida.with_suffix(".informe.json").exists())

    def test_no_sobrescribe(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            salida = raiz / "modelo.obj"
            salida.write_text("existente")
            with self.assertRaises(ValueError):
                reconstruir_superficie_auto(raiz / "nube.ply", salida)
            self.assertEqual(salida.read_text(), "existente")


if __name__ == "__main__":
    unittest.main()
