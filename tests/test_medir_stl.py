import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from medir_stl import medir

class Medidas(unittest.TestCase):
    def setUp(self):
        a=(0.,0.,0.);b=(1.,0.,0.);c=(0.,1.,0.);d=(0.,0.,1.)
        self.tetra=[(a,c,b),(a,b,d),(a,d,c),(b,c,d)]
    def test_tetra_cerrado(self):
        r=medir(self.tetra,'cm')
        self.assertTrue(r['volumen_estimado_valido_topologicamente'])
        self.assertAlmostEqual(r['volumen_mm3'],1000/6,4)
        self.assertEqual(r['dimensiones_mm'],[10,10,10])
    def test_abierto_sin_volumen(self):
        r=medir(self.tetra[:-1])
        self.assertIsNone(r['volumen_mm3'])
    def test_unidad_obligatoria_valida(self):
        with self.assertRaises(ValueError): medir(self.tetra,'desconocida')
    def test_orientacion_incorrecta(self):
        t=self.tetra.copy(); a,b,c=t[0];t[0]=(a,c,b)
        self.assertIsNone(medir(t)['volumen_mm3'])
if __name__=='__main__': unittest.main()
