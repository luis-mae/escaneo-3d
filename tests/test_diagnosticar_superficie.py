import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from diagnosticar_superficie import diagnosticar

A=(0.,0.,0.); B=(1.,0.,0.); C=(0.,1.,0.); D=(0.,0.,1.)

class TestDiagnosticoSuperficie(unittest.TestCase):
    def test_tetraedro_cerrado(self):
        result=diagnosticar([(A,B,C),(A,D,B),(B,D,C),(C,D,A)])
        self.assertTrue(result['malla_cerrada_por_aristas'])
        self.assertEqual(result['bucles_cerrados'],0)

    def test_tetraedro_abierto(self):
        result=diagnosticar([(A,D,B),(B,D,C),(C,D,A)])
        self.assertEqual(result['aristas_abiertas'],3)
        self.assertEqual(result['bucles_cerrados'],1)
        self.assertEqual(result['longitudes_bucles'],[3])

    def test_arista_no_manifold(self):
        E=(0.,-1.,0.)
        result=diagnosticar([(A,B,C),(B,A,D),(A,B,E)])
        self.assertEqual(result['aristas_no_manifold'],1)
        self.assertFalse(result['malla_cerrada_por_aristas'])

    def test_cara_degenerada(self):
        with self.assertRaises(ValueError):
            diagnosticar([(A,A,B)])

    def test_vacia(self):
        result=diagnosticar([])
        self.assertFalse(result['malla_cerrada_por_aristas'])
