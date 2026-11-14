import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from optimizar_stl import optimizar

class TestOptimizar(unittest.TestCase):
    def test_soldar_cerca_de_borde_de_celda(self):
        caras=[((0.,0.,0.),(1.,0.,0.),(0.,1.,0.)),
               ((0.0099,0.,0.),(1.,0.,0.),(0.,0.,1.))]
        out,stats=optimizar(caras,0.01)
        self.assertEqual(stats['vertices_finales'],4)
        self.assertEqual(len(out),2)
    def test_eliminar_cara_colapsada(self):
        caras=[((0.,0.,0.),(0.0001,0.,0.),(0.,1.,0.)),
               ((0.,0.,0.),(1.,0.,0.),(0.,1.,0.))]
        out,stats=optimizar(caras,0.001)
        self.assertEqual(len(out),1)
        self.assertEqual(stats['degenerados_eliminados'],1)
    def test_tolerancia_invalida(self):
        with self.assertRaises(ValueError): optimizar([],0)
        with self.assertRaises(ValueError): optimizar([],float('nan'))

if __name__=='__main__':unittest.main()
