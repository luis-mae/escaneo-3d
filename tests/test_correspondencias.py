import unittest
from pathlib import Path
from tools.correspondencias import comparar


class TestCorrespondencias(unittest.TestCase):
    def test_minimo_invalido(self):
        with self.assertRaises(ValueError):
            comparar(Path('a.jpg'), Path('b.jpg'), minimo=3)

    def test_archivos_inexistentes(self):
        try:
            import cv2  # noqa
        except ImportError:
            self.skipTest('OpenCV opcional no instalado')
        with self.assertRaises(ValueError):
            comparar(Path('/no-existe-a.jpg'), Path('/no-existe-b.jpg'))
