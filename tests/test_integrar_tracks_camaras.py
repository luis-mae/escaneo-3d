import unittest
import numpy as np
from tools.integrar_tracks_camaras import integrar_tracks


class TestIntegracion(unittest.TestCase):
    def setUp(self):
        K = [[700, 0, 320], [0, 700, 240], [0, 0, 1]]
        self.cameras = {str(i): {'K': K, 'R': np.eye(3).tolist(), 't': [-i * .4, 0, 0]} for i in range(3)}
        self.pts = {str(i): [[320 + 700 * (.2 - i * .4) / 3, 240 + 700 * .1 / 3]] for i in range(3)}

    def test_triangulacion_tres_vistas(self):
        r = integrar_tracks(self.cameras, self.pts, [{'0': 0, '1': 0, '2': 0}])
        self.assertEqual(r['aceptados'], 1)
        np.testing.assert_allclose(r['puntos'][0], [.2, .1, 3], atol=1e-6)

    def test_indice_inexistente_descartado(self):
        r = integrar_tracks(self.cameras, self.pts, [{'0': 0, '1': 5}])
        self.assertEqual(r['tracks_descartados_entrada'], 1)

    def test_outlier_rechazado(self):
        self.pts['2'][0][0] += 90
        r = integrar_tracks(self.cameras, self.pts, [{'0': 0, '1': 0, '2': 0}])
        self.assertEqual(r['aceptados'], 0)

    def test_track_incompleto(self):
        r = integrar_tracks(self.cameras, self.pts, [{'0': 0}])
        self.assertEqual(r['tracks_descartados_entrada'], 1)

    def test_falta_camara(self):
        r = integrar_tracks(self.cameras, self.pts, [{'0': 0, 'desconocida': 0}])
        self.assertEqual(r['tracks_descartados_entrada'], 1)


if __name__ == '__main__':
    unittest.main()
