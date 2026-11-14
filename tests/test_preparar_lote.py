import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from preparar_lote import ejecutar_lote
from reparar_stl import escribir_binario


class PruebaLote(unittest.TestCase):
    def test_lote_mixto(self):
        with tempfile.TemporaryDirectory() as tmp:
            origen, salida = Path(tmp) / 'entrada', Path(tmp) / 'salida'
            origen.mkdir()
            escribir_binario(origen / 'bueno.stl', [((0, 0, 0), (1, 0, 0), (0, 1, 0))])
            (origen / 'malo.stl').write_bytes(b'no es un STL')
            (origen / 'ignorar.txt').write_text('x')
            resultado = ejecutar_lote(origen, salida)
            self.assertEqual(resultado['total'], 2)
            self.assertEqual(resultado['correctos'], 1)
            self.assertEqual(resultado['errores'], 1)
            self.assertTrue((salida / 'bueno_preparado.stl').exists())
            self.assertTrue((salida / 'resumen_lote.json').exists())

    def test_rechaza_salida_dentro_de_entrada(self):
        with tempfile.TemporaryDirectory() as tmp:
            origen = Path(tmp)
            with self.assertRaises(ValueError):
                ejecutar_lote(origen, origen / 'salida')

    def test_rechaza_origen_vacio(self):
        with tempfile.TemporaryDirectory() as tmp:
            origen, salida = Path(tmp) / 'entrada', Path(tmp) / 'salida'
            origen.mkdir()
            with self.assertRaises(ValueError):
                ejecutar_lote(origen, salida)


if __name__ == '__main__':
    unittest.main()
