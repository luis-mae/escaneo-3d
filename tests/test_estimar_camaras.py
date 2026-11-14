import tempfile
import unittest
from pathlib import Path
import cv2
import numpy as np
from tools.estimar_camaras import estimar_pose


class EstimarCamarasTests(unittest.TestCase):
    def test_rechaza_focal_invalida(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'a.png'
            cv2.imwrite(str(p), np.zeros((100, 100), dtype=np.uint8))
            with self.assertRaises(ValueError):
                estimar_pose(p, p, 0)

    def test_rechaza_fotos_vacias(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / 'a.png', Path(tmp) / 'b.png'
            cv2.imwrite(str(a), np.zeros((100, 100), dtype=np.uint8))
            cv2.imwrite(str(b), np.zeros((100, 100), dtype=np.uint8))
            result = estimar_pose(a, b, 100)
            self.assertEqual(result['estado'], 'insuficiente')

    def test_rechaza_resoluciones_distintas(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / 'a.png', Path(tmp) / 'b.png'
            cv2.imwrite(str(a), np.zeros((100, 100), dtype=np.uint8))
            cv2.imwrite(str(b), np.zeros((120, 100), dtype=np.uint8))
            with self.assertRaises(ValueError):
                estimar_pose(a, b, 100)


if __name__ == '__main__':
    unittest.main()
