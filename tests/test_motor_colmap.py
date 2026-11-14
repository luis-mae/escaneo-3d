import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tools.motor_colmap import ejecutar_colmap


class TestMotorColmap(unittest.TestCase):
    def test_rechaza_colmap_ausente(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            fotos = raiz / "fotos"
            fotos.mkdir()
            (fotos / "1.jpg").write_bytes(b"foto")
            with patch("tools.motor_colmap.shutil.which", return_value=None):
                with self.assertRaises(FileNotFoundError):
                    ejecutar_colmap(fotos, raiz / "salida")

    def test_no_sobrescribe_salida(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            fotos = raiz / "fotos"
            fotos.mkdir()
            (fotos / "1.jpg").write_bytes(b"foto")
            salida = raiz / "salida"
            salida.mkdir()
            with self.assertRaises(FileExistsError):
                ejecutar_colmap(fotos, salida)

    def test_rechaza_salida_dentro_de_fotos(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            fotos = raiz / "fotos"
            fotos.mkdir()
            (fotos / "1.jpg").write_bytes(b"foto")
            with self.assertRaises(ValueError):
                ejecutar_colmap(fotos, fotos / "salida")

    def test_informe_fallo_comando(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            fotos = raiz / "fotos"
            fotos.mkdir()
            (fotos / "1.jpg").write_bytes(b"foto")
            salida = raiz / "salida"
            with patch("tools.motor_colmap.shutil.which", return_value="/usr/bin/colmap"), \
                 patch("tools.motor_colmap.subprocess.run",
                       return_value=SimpleNamespace(returncode=1, stdout="", stderr="error")):
                with self.assertRaises(RuntimeError):
                    ejecutar_colmap(fotos, salida)
            self.assertTrue((salida / "informe_colmap.json").exists())


if __name__ == "__main__":
    unittest.main()
