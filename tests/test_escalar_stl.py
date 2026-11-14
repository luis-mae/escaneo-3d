import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from escalar_stl import escalar
from reparar_stl import escribir_binario
from verificar_stl import leer_stl


class EscalarSTLTests(unittest.TestCase):
    def test_escala_dimension_conocida(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d)/'a.stl', Path(d)/'b.stl'
            escribir_binario(a, [((0,0,0),(2,0,0),(0,1,0))])
            r = escalar(a, b, 'x', 20)
            self.assertAlmostEqual(r['factor'], 10)
            self.assertAlmostEqual(max(v[0] for f in leer_stl(b) for v in f), 20)
            self.assertTrue(a.exists())

    def test_rechaza_medida_invalida(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d)/'a.stl', Path(d)/'b.stl'
            escribir_binario(a, [((0,0,0),(2,0,0),(0,1,0))])
            for medida in (0, -2, float('nan'), float('inf')):
                with self.assertRaises(ValueError):
                    escalar(a, b, 'x', medida)

    def test_rechaza_sobrescritura(self):
        with tempfile.TemporaryDirectory() as d:
            a = Path(d)/'a.stl'
            escribir_binario(a, [((0,0,0),(2,0,0),(0,1,0))])
            with self.assertRaises(ValueError):
                escalar(a, a, 'x', 20)


if __name__ == '__main__':
    unittest.main()
