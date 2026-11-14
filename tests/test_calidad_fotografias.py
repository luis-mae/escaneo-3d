import tempfile
import unittest
from pathlib import Path
from PIL import Image
from tools.calidad_fotografias import analizar_carpeta


class CalidadFotografiasTest(unittest.TestCase):
    def test_oscuridad_y_duplicados(self):
        with tempfile.TemporaryDirectory() as tmp:
            carpeta = Path(tmp)
            Image.new('RGB', (800, 800), (0, 0, 0)).save(carpeta / '01.png')
            Image.new('RGB', (800, 800), (0, 0, 0)).save(carpeta / '02.png')
            salida = analizar_carpeta(carpeta)
            self.assertEqual(salida['cantidad'], 2)
            self.assertIn('subexposicion', salida['imagenes'][0]['problemas'])
            self.assertTrue(any('posible_duplicado' in p for p in salida['imagenes'][1]['problemas']))

    def test_archivo_corrupto(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / 'mala.jpg'
            ruta.write_bytes(b'no es una foto')
            self.assertEqual(analizar_carpeta(Path(tmp))['imagenes'][0]['estado'], 'no_decodificable')


if __name__ == '__main__':
    unittest.main()
