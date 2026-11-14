import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from cerrar_agujeros import cerrar

class TestCierre(unittest.TestCase):
    def test_tetraedro_sin_tapa(self):
        a=(0.,0.,0.);b=(1.,0.,0.);c=(0.,1.,0.);d=(0.,0.,1.)
        faces=[(a,d,b),(b,d,c),(c,d,a)]
        result,stats=cerrar(faces)
        self.assertEqual(stats['agujeros_cerrados'],1)
        self.assertEqual(len(result),6)
    def test_no_modifica_cerrado(self):
        a=(0.,0.,0.);b=(1.,0.,0.);c=(0.,1.,0.);d=(0.,0.,1.)
        faces=[(a,d,b),(b,d,c),(c,d,a),(a,b,c)]
        result,stats=cerrar(faces)
        self.assertEqual(stats['agujeros_cerrados'],0)
        self.assertEqual(len(result),4)
if __name__=='__main__':unittest.main()
