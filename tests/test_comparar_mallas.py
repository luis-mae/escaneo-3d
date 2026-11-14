import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from comparar_mallas import comparar

TETRA = [((0,0,0),(0,1,0),(1,0,0)), ((0,0,0),(1,0,0),(0,0,1)), ((0,0,0),(0,0,1),(0,1,0)), ((1,0,0),(0,1,0),(0,0,1))]

class CompararTest(unittest.TestCase):
    def test_identico(self):
        d=comparar(TETRA,TETRA)
        self.assertEqual(d['alertas'],[])
        self.assertEqual(d['reduccion_pct'],0)
    def test_cambio_escala(self):
        doble=[tuple(tuple(x*2 for x in p) for p in tri) for tri in TETRA]
        d=comparar(TETRA,doble)
        self.assertTrue(d['revision_recomendada'])
    def test_cambio_topologia(self):
        d=comparar(TETRA,TETRA[:-1])
        self.assertTrue(d['revision_recomendada'])
    def test_tolerancia_invalida(self):
        with self.assertRaises(ValueError): comparar(TETRA,TETRA,tolerancia_pct=-1)

if __name__=='__main__': unittest.main()
