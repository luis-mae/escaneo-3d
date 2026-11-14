import unittest
import numpy as np
from tools.pipeline_superficie import procesar

class TestPipelineSuperficie(unittest.TestCase):
    def test_tetraedro_cerrado(self):
        v, f, r = procesar([[0,0,0],[1,0,0],[0,1,0],[0,0,1]], 2)
        self.assertEqual(len(f), 4)
        self.assertTrue(r['malla_cerrada_por_aristas'])
        self.assertFalse(r['apto_para_impresion'])
    def test_alpha_insuficiente(self):
        with self.assertRaises(ValueError):
            procesar([[0,0,0],[1,0,0],[0,1,0],[0,0,1]], 0.01)
    def test_entrada_invalida(self):
        with self.assertRaises(ValueError):
            procesar([[0,0,0],[1,0,0],[0,1,0]], 2)
