import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from auditar_malla import auditar

T=[(0.,0.,0.),(1.,0.,0.),(0.,1.,0.),(0.,0.,1.)]
F=[(T[0],T[2],T[1]),(T[0],T[1],T[3]),(T[0],T[3],T[2]),(T[1],T[2],T[3])]
class Auditoria(unittest.TestCase):
    def test_tetraedro(self):
        r=auditar(F)
        self.assertEqual(r['caracteristica_euler'],2)
        self.assertEqual(r['componentes_conectados'],1)
        self.assertTrue(r['apta_para_revision_de_impresion'])
    def test_abierta(self):
        r=auditar(F[:-1]);self.assertFalse(r['apta_para_revision_de_impresion'])
        self.assertEqual(r['aristas_abiertas'],3)
    def test_componentes(self):
        shifted=[tuple(tuple(v+10 for v in p) for p in tri) for tri in F]
        r=auditar(F+shifted)
        self.assertEqual(r['componentes_conectados'],2)
        self.assertFalse(r['apta_para_revision_de_impresion'])
if __name__=='__main__': unittest.main()
