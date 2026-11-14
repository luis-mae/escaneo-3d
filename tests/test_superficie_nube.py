import unittest
import tempfile
from pathlib import Path
import numpy as np
from tools.superficie_nube import generar_superficie, guardar_obj


class TestSuperficieNube(unittest.TestCase):
    def test_tetraedro(self):
        p = [[0,0,0], [1,0,0], [0,1,0], [0,0,1]]
        vertices, caras, volumen = generar_superficie(p)
        self.assertEqual(len(caras), 4)
        self.assertAlmostEqual(volumen, 1/6)
        self.assertEqual(len(vertices), 4)

    def test_coplanar_rechazado(self):
        with self.assertRaises(ValueError):
            generar_superficie([[0,0,0], [1,0,0], [0,1,0], [1,1,0]])

    def test_nan_rechazado(self):
        with self.assertRaises(ValueError):
            generar_superficie([[0,0,0], [1,0,0], [0,1,0], [float('nan'),0,1]])

    def test_exportacion_obj(self):
        v, f, _ = generar_superficie([[0,0,0], [1,0,0], [0,1,0], [0,0,1]])
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / 'superficie.obj'
            guardar_obj(ruta, v, f)
            texto = ruta.read_text()
            self.assertEqual(texto.count('\nv '), 4)
            self.assertEqual(texto.count('\nf '), 4)

    def test_normales_exteriores(self):
        v, f, _ = generar_superficie([[0,0,0], [1,0,0], [0,1,0], [0,0,1]])
        centro = v.mean(axis=0)
        for a, b, c in f:
            normal = np.cross(v[b]-v[a], v[c]-v[a])
            self.assertGreater(np.dot(normal, v[a]-centro), 0)


if __name__ == '__main__':
    unittest.main()
