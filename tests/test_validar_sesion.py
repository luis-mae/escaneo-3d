import tempfile
import unittest
from pathlib import Path
from tools.validar_sesion import validar_sesion

class TestSesion(unittest.TestCase):
    def test_cantidad_minima(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            for i in range(3):
                (p / f'{i}.jpg').write_bytes(bytes([65+i]) * 30000)
            self.assertEqual(validar_sesion(p, 3)['estado'], 'apta_para_intentar')
            self.assertEqual(validar_sesion(p, 4)['estado'], 'revisar')
    def test_vacias(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / 'a.jpg').write_bytes(b'x' * 30000)
            (p / 'b.jpg').touch()
            self.assertEqual(validar_sesion(p, 2)['imagenes_vacias'], ['b.jpg'])
    def test_no_existe(self):
        with self.assertRaises(FileNotFoundError):
            validar_sesion(Path('/no/existe/escaneo'))

if __name__ == '__main__':
    unittest.main()
