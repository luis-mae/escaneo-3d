import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from optimizar_malla import optimizar, procesar
from reparar_stl import escribir_binario

class TestOptimizar(unittest.TestCase):
    def test_celda_invalida(self):
        for n in (0, -1, float('nan'), float('inf')):
            with self.assertRaises(ValueError): optimizar([], n)

    def test_triangulo_conservado(self):
        cara = ((0.,0.,0.),(2.,0.,0.),(0.,2.,0.))
        self.assertEqual(len(optimizar([cara], 0.1)), 1)

    def test_colapso(self):
        cara = ((0.,0.,0.),(0.01,0.,0.),(0.,0.01,0.))
        self.assertEqual(optimizar([cara], 1), [])

    def test_duplicados(self):
        cara = ((0.,0.,0.),(2.,0.,0.),(0.,2.,0.))
        self.assertEqual(len(optimizar([cara, cara], 0.1)), 1)

    def test_no_sobrescribir(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as d:
            f = Path(d)/'m.stl'
            escribir_binario(f, [((0.,0.,0.),(2.,0.,0.),(0.,2.,0.))])
            with self.assertRaises(ValueError): procesar(f, f, 0.1)

    def test_informe(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as d:
            f, out = Path(d)/'m.stl', Path(d)/'out.stl'
            cara = ((0.,0.,0.),(2.,0.,0.),(0.,2.,0.))
            escribir_binario(f, [cara, cara])
            info = procesar(f, out, 0.1)
            self.assertEqual(info['triangulos_antes'], 2)
            self.assertEqual(info['triangulos_despues'], 1)
            self.assertTrue(out.exists())

if __name__ == '__main__': unittest.main()
