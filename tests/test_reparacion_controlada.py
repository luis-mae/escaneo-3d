import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from reparar_stl import escribir_binario
from reparacion_controlada import reparar_controlado

A=(0.,0.,0.); B=(1.,0.,0.); C=(0.,1.,0.); D=(0.,0.,1.)
CARA_ABIERTA=[(A,D,B),(B,D,C),(C,D,A)]

class TestReparacionControlada(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.src=Path(self.tmp.name)/'original.stl'
        self.dst=Path(self.tmp.name)/'reparado.stl'
        escribir_binario(self.src,CARA_ABIERTA)

    def test_cierra_agujero_y_preserva_original(self):
        original=self.src.read_bytes()
        report=reparar_controlado(self.src,self.dst,cerrar_pequenos=True)
        self.assertEqual(report['cierre']['agujeros_cerrados'],1)
        self.assertEqual(report['despues']['aristas_abiertas'],0)
        self.assertEqual(self.src.read_bytes(),original)

    def test_sin_cierre_mantiene_borde(self):
        report=reparar_controlado(self.src,self.dst)
        self.assertEqual(report['cierre']['agujeros_cerrados'],0)
        self.assertGreater(report['despues']['aristas_abiertas'],0)

    def test_no_sobrescribe_entrada(self):
        with self.assertRaises(ValueError):
            reparar_controlado(self.src,self.src)

    def test_no_sobrescribe_salida(self):
        self.dst.write_bytes(b'previo')
        with self.assertRaises(FileExistsError):
            reparar_controlado(self.src,self.dst)
        self.assertEqual(self.dst.read_bytes(),b'previo')

    def test_valida_limite(self):
        with self.assertRaises(ValueError):
            reparar_controlado(self.src,self.dst,True,2)

if __name__=='__main__': unittest.main()
