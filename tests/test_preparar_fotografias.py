import tempfile
import unittest
from pathlib import Path
from PIL import Image
from tools.preparar_fotografias import preparar


class TestPreparacion(unittest.TestCase):
    def test_redimensiona_y_preserva_original(self):
        with tempfile.TemporaryDirectory() as t:
            src, dst = Path(t) / 'src', Path(t) / 'dst'
            src.mkdir()
            Image.new('RGB', (1200, 600), 'white').save(src / 'a.png')
            resultado = preparar(src, dst, 600)
            self.assertEqual(resultado['total_ok'], 1)
            with Image.open(dst / 'foto_0000.jpg') as im:
                self.assertEqual(im.size, (600, 300))
            self.assertTrue((src / 'a.png').exists())
            self.assertTrue((dst / 'manifest.json').exists())

    def test_no_amplia(self):
        with tempfile.TemporaryDirectory() as t:
            src, dst = Path(t) / 'src', Path(t) / 'dst'
            src.mkdir()
            Image.new('RGB', (300, 200)).save(src / 'a.jpg')
            preparar(src, dst)
            with Image.open(dst / 'foto_0000.jpg') as im:
                self.assertEqual(im.size, (300, 200))

    def test_parametros(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):
                preparar(Path(t), Path(t), 100)
            with self.assertRaises(ValueError):
                preparar(Path(t), Path(t))


if __name__ == '__main__':
    unittest.main()
