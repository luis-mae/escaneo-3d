import tempfile
import unittest
from pathlib import Path
from PIL import Image
from tools.seleccionar_fotografias import seleccionar


class SeleccionTest(unittest.TestCase):
    def test_descarta_duplicado_y_oscuridad(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            Image.new('RGB', (800, 800), 'black').save(p / 'oscura.png')
            Image.new('RGB', (800, 800), 'black').save(p / 'duplicada.png')
            resultado = seleccionar(p)
            self.assertEqual(resultado['cantidad_seleccionadas'], 0)
            self.assertEqual(len(resultado['descartadas']), 2)

    def test_limite_invalido(self):
        with self.assertRaises(ValueError):
            seleccionar(Path('.'), 0)

    def test_carpeta_vacia(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(seleccionar(Path(d))['cantidad_seleccionadas'], 0)


if __name__ == '__main__':
    unittest.main()
