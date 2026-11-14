import tempfile
import unittest
from pathlib import Path
from tools.validar_sesion import validar_sesion


class DuplicadosSesionTest(unittest.TestCase):
    def test_duplicados_no_cuentan_como_vistas(self):
        with tempfile.TemporaryDirectory() as carpeta:
            base = Path(carpeta)
            (base / 'a.jpg').write_bytes(b'foto' * 6000)
            (base / 'b.jpg').write_bytes(b'foto' * 6000)
            resultado = validar_sesion(base, 2)
            self.assertEqual(resultado['imagenes_unicas'], 1)
            self.assertEqual(len(resultado['imagenes_duplicadas']), 1)
            self.assertEqual(resultado['estado'], 'revisar')

    def test_fotos_distintas(self):
        with tempfile.TemporaryDirectory() as carpeta:
            base = Path(carpeta)
            (base / 'a.jpg').write_bytes(b'a' * 25000)
            (base / 'b.jpg').write_bytes(b'b' * 25000)
            resultado = validar_sesion(base, 2)
            self.assertEqual(resultado['imagenes_unicas'], 2)
            self.assertEqual(resultado['estado'], 'apta_para_intentar')
