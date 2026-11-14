import tempfile
import unittest
from pathlib import Path
import cv2
import numpy as np
from tools.tracks_desde_fotos import emparejar_descriptores, extraer_tracks


class TestTracksDesdeFotos(unittest.TestCase):
    def test_reciprocos(self):
        a = np.array([[0]*32, [255]*32, [85]*32], dtype=np.uint8)
        b = a[[2, 0, 1]].copy()
        self.assertEqual(emparejar_descriptores(a, b), [(0, 1), (1, 2), (2, 0)])

    def test_descriptores_vacios(self):
        self.assertEqual(emparejar_descriptores(None, None), [])

    def test_ratio_invalido(self):
        with self.assertRaises(ValueError):
            emparejar_descriptores(None, None, ratio=1.2)

    def test_fotos_inexistentes(self):
        with self.assertRaises(ValueError):
            extraer_tracks(['no_existe_a.jpg', 'no_existe_b.jpg'])

    def test_nombres_duplicados(self):
        with self.assertRaises(ValueError):
            extraer_tracks(['a/foto.jpg', 'b/foto.jpg'])

    def test_fotos_sin_textura(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = [Path(tmp)/f'{i}.png' for i in range(2)]
            for path in paths:
                cv2.imwrite(str(path), np.zeros((128, 128), dtype=np.uint8))
            result = extraer_tracks(paths)
            self.assertEqual(result['total_tracks'], 0)
            self.assertEqual(result['pares'][0]['estado'], 'insuficiente')

if __name__ == '__main__':
    unittest.main()
