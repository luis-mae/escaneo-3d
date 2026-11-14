import unittest
from unittest.mock import patch
import numpy as np
from tools.pipeline_fotos_multivista import camaras_desde_poses, procesar


class PipelineFotosTest(unittest.TestCase):
    def test_camaras(self):
        pose = {'R': np.eye(3).tolist(), 't': [0, 0, 0]}
        c = camaras_desde_poses(['a', 'b'], [pose, pose], 500, 640, 480)
        self.assertEqual(c['a']['K'][0][2], 320)
        self.assertEqual(c['b']['K'][1][2], 240)

    def test_calibracion_invalida(self):
        with self.assertRaises(ValueError):
            camaras_desde_poses(['a'], [], 500, 640, 480)

    def test_fotos_insuficientes(self):
        with self.assertRaises(ValueError):
            procesar(['a.jpg', 'b.jpg'], 500)

    @patch('cv2.imread')
    @patch('tools.pipeline_fotos_multivista.integrar_tracks')
    @patch('tools.pipeline_fotos_multivista.estimar_secuencia')
    @patch('tools.pipeline_fotos_multivista.extraer_tracks')
    def test_integracion_mock(self, tracks, poses, integrar, imread):
        imread.return_value = np.zeros((480, 640, 3), dtype=np.uint8)
        tracks.return_value = {'pares': [{'estado':'aceptado'}]*2, 'total_tracks': 3,
                              'puntos_por_imagen': {}, 'tracks': []}
        pose = {'R': np.eye(3).tolist(), 't': [0, 0, 0]}
        poses.return_value = {'estado':'experimental', 'poses':[pose]*3}
        integrar.return_value = {'puntos': [[0, 0, 1]]*3, 'aceptados':3,
                                  'rechazados':0, 'tracks_descartados_entrada':0}
        xyz, informe = procesar(['a.jpg', 'b.jpg', 'c.jpg'], 500)
        self.assertEqual(len(xyz), 3)
        self.assertEqual(informe['estado'], 'experimental_no_metrico')


if __name__ == '__main__':
    unittest.main()
