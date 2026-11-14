import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from reparar_stl import escribir_binario
from preparar_impresion import preparar


class TestPrepararImpresion(unittest.TestCase):
    def test_limpieza_y_reporte(self):
        with tempfile.TemporaryDirectory() as d:
            original, salida = Path(d)/'original.stl', Path(d)/'salida.stl'
            tri = ((0., 0., 0.), (1., 0., 0.), (0., 1., 0.))
            escribir_binario(original, [tri, tri])
            reporte = preparar(original, salida)
            self.assertEqual(reporte['limpieza']['duplicados_eliminados'], 1)
            self.assertTrue(salida.exists())
            self.assertEqual(reporte['despues']['triangulos'], 1)
            self.assertTrue(reporte['advertencias'])

    def test_no_sobrescribe(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d)/'pieza.stl'
            escribir_binario(ruta, [((0., 0., 0.), (1., 0., 0.), (0., 1., 0.))])
            with self.assertRaises(ValueError):
                preparar(ruta, ruta)


if __name__ == '__main__':
    unittest.main()
