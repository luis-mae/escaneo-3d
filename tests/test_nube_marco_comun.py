import unittest
import numpy as np
from tools.nube_marco_comun import reconstruir_observaciones

class TestMarcoComun(unittest.TestCase):
    def setUp(self):
        K = [[800,0,320],[0,800,240],[0,0,1]]
        self.camaras = [{'K':K,'R':np.eye(3).tolist(),'t':[-i*.3,0,0]} for i in range(3)]

    def pista(self, xyz, indices=(0,1,2), identificador='p'):
        obs=[]
        for i in indices:
            x,y,z=xyz
            obs.append({'camara':i,'xy':[800*(x-i*.3)/z+320,800*y/z+240]})
        return {'id':identificador,'observaciones':obs}

    def test_tres_camaras_mismo_marco(self):
        r=reconstruir_observaciones(self.camaras,[self.pista([.2,.1,3])])
        self.assertEqual(r['aceptados'],1)
        np.testing.assert_allclose(r['puntos'][0],[.2,.1,3],atol=1e-6)

    def test_rechaza_error_reproyeccion(self):
        p=self.pista([.2,.1,3]); p['observaciones'][2]['xy'][0]+=30
        self.assertEqual(reconstruir_observaciones(self.camaras,[p])['aceptados'],0)

    def test_rechaza_observaciones_repetidas(self):
        p=self.pista([.2,.1,3],(0,1)); p['observaciones'][1]['camara']=0
        self.assertEqual(reconstruir_observaciones(self.camaras,[p])['rechazados'],1)

    def test_rechaza_punto_detras(self):
        self.assertEqual(reconstruir_observaciones(self.camaras,[self.pista([.2,.1,-3])])['aceptados'],0)

    def test_dos_vistas_validas(self):
        self.assertEqual(reconstruir_observaciones(self.camaras,[self.pista([.1,.2,2],(0,2))])['aceptados'],1)

if __name__=='__main__': unittest.main()
