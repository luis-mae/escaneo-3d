import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from orientar_stl import orientar

class TestOrientar(unittest.TestCase):
    def test_tetraedro_orientado(self):
        a=(0,0,0);b=(1,0,0);c=(0,1,0);d=(0,0,1)
        faces=[(a,c,b),(a,b,d),(a,d,c),(b,c,d)]
        faces[1]=(a,d,b)
        out,stats=orientar(faces)
        self.assertEqual(stats['componentes'],1)
        self.assertEqual(stats['componentes_no_cerrados_o_conflictivos'],0)
        self.assertEqual(stats['conflictos_orientacion'],0)
        vol=sum(p[0]*(q[1]*r[2]-q[2]*r[1])+p[1]*(q[2]*r[0]-q[0]*r[2])+p[2]*(q[0]*r[1]-q[1]*r[0]) for p,q,r in out)/6
        self.assertGreater(vol,0)
    def test_abierta_no_promete_cierre(self):
        out,stats=orientar([((0,0,0),(1,0,0),(0,1,0))])
        self.assertEqual(stats['componentes_no_cerrados_o_conflictivos'],1)
        self.assertEqual(len(out),1)
    def test_degenerada(self):
        with self.assertRaises(ValueError): orientar([((0,0,0),(0,0,0),(1,0,0))])

if __name__=='__main__': unittest.main()
