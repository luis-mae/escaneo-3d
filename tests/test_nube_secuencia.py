import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tools.nube_secuencia import procesar_secuencia

class TestNubeSecuencia(unittest.TestCase):
    def test_requiere_dos(self):
        with self.assertRaises(ValueError):
            procesar_secuencia(['a.jpg'], 100, 'salida')

    def test_pares_independientes(self):
        with tempfile.TemporaryDirectory() as d:
            with patch('tools.nube_secuencia.reconstruir_par', return_value={'estado': 'insuficiente', 'motivo': 'sin coincidencias'}):
                result = procesar_secuencia(['a.jpg', 'b.jpg', 'c.jpg'], 100, d)
            self.assertEqual(len(result['pares']), 2)
            self.assertFalse(result['fusionadas'])
            self.assertTrue((Path(d) / 'informe.json').exists())

    def test_exporta_ply_por_par(self):
        with tempfile.TemporaryDirectory() as d:
            fake = {'estado': 'experimental', 'aceptados': 1, 'puntos': [[1, 2, 3]]}
            with patch('tools.nube_secuencia.reconstruir_par', return_value=fake):
                result = procesar_secuencia(['a.jpg', 'b.jpg'], 100, d)
            self.assertEqual(result['pares'][0]['archivo'], 'par_000.ply')
            self.assertTrue((Path(d) / 'par_000.ply').exists())
