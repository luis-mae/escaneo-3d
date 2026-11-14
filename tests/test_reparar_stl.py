import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from reparar_stl import limpiar, escribir_binario, reparar
from verificar_stl import analizar

A = ((0., 0., 0.), (1., 0., 0.), (0., 1., 0.))
B = ((0., 0., 0.), (0., 0., 0.), (0., 1., 0.))

class TestRepararSTL(unittest.TestCase):
    def test_limpieza(self):
        caras, stats = limpiar([A, A, B])
        self.assertEqual(len(caras), 1)
        self.assertEqual(stats['duplicados_eliminados'], 1)
        self.assertEqual(stats['degenerados_eliminados'], 1)

    def test_archivo(self):
        with tempfile.TemporaryDirectory() as d:
            entrada, salida = Path(d)/'entrada.stl', Path(d)/'salida.stl'
            escribir_binario(entrada, [A, A, B])
            reporte = reparar(entrada, salida)
            self.assertEqual(reporte['diagnostico']['triangulos'], 1)
            self.assertEqual(analizar(salida)['triangulos_degenerados'], 0)
            self.assertFalse(reporte['diagnostico']['malla_cerrada_por_aristas'])

    def test_no_sobrescribir(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'modelo.stl'
            escribir_binario(p, [A])
            with self.assertRaises(ValueError):
                reparar(p, p)

if __name__ == '__main__':
    unittest.main()
