import tempfile
import unittest
from pathlib import Path
import numpy as np
from tools.nube_dos_vistas import guardar_ply, reconstruir_par

class NubeDosVistasTests(unittest.TestCase):
    def test_exporta_ply(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'nube.ply'
            guardar_ply([[0,1,2],[3,4,5]], p)
            text = p.read_text()
            self.assertIn('element vertex 2', text)
            self.assertIn('3 4 5', text)
    def test_rechaza_nube_invalida(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError): guardar_ply([[1,2]], Path(tmp)/'x.ply')
            with self.assertRaises(ValueError): guardar_ply([[1,2,np.nan]], Path(tmp)/'x.ply')
    def test_rechaza_imagenes_ausentes(self):
        with self.assertRaises(ValueError): reconstruir_par('/no/a.jpg','/no/b.jpg',800)
    def test_rechaza_focal_invalida(self):
        with self.assertRaises(ValueError): reconstruir_par('/no/a.jpg','/no/b.jpg',0)
