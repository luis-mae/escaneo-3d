import struct
import tempfile
import unittest
from pathlib import Path
from tools.inspeccionar_imagenes import dimensiones, inspeccionar


class InspeccionTest(unittest.TestCase):
    def test_png_dimensiones(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'foto.png'
            p.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00\x00\x00\rIHDR' + struct.pack('>II', 1920, 1080))
            self.assertEqual(dimensiones(p), (1920, 1080))
            self.assertEqual(inspeccionar(Path(d))['imagenes'][0]['estado'], 'resolucion_aceptable')

    def test_png_baja_resolucion(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'foto.png'
            p.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00\x00\x00\rIHDR' + struct.pack('>II', 300, 500))
            self.assertEqual(inspeccionar(Path(d))['imagenes'][0]['estado'], 'resolucion_baja')

    def test_archivo_invalido(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'foto.jpg'
            p.write_bytes(b'not a jpeg')
            self.assertIsNone(dimensiones(p))
            self.assertEqual(inspeccionar(Path(d))['imagenes'][0]['estado'], 'no_verificable')

    def test_jpeg_dimensiones(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'foto.jpg'
            p.write_bytes(b'\xff\xd8\xff\xc0\x00\x11\x08' + struct.pack('>HH', 1200, 1600) + b'\x03' + b'\x00'*10)
            self.assertEqual(dimensiones(p), (1600, 1200))
