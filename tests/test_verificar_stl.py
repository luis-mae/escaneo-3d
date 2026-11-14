import tempfile
import unittest
from pathlib import Path
from tools.verificar_stl import analizar

class TestSTL(unittest.TestCase):
    def test_triangulo_abierto_ascii(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'triangle.stl'
            p.write_text('solid t\nfacet normal 0 0 1\nouter loop\nvertex 0 0 0\nvertex 1 0 0\nvertex 0 1 0\nendloop\nendfacet\nendsolid t\n')
            result = analizar(p)
            self.assertEqual(result['triangulos'], 1)
            self.assertEqual(result['aristas_abiertas'], 3)
            self.assertFalse(result['malla_cerrada_por_aristas'])

if __name__ == '__main__':
    unittest.main()
