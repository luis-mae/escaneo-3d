import unittest
import numpy as np
from tools.ajuste_multivista import ajustar


class TestAjusteMultivista(unittest.TestCase):
    def setUp(self):
        K = np.array([[600., 0, 320], [0, 600, 240], [0, 0, 1]])
        self.cams = [{'K': K.tolist(), 'R': np.eye(3).tolist(), 't': [-i * .3, 0., 0.]} for i in range(3)]
        self.points = np.array([[x, y, 3 + .2*x] for x in (-.5, 0, .5) for y in (-.4, .4)])
        self.obs = []
        for j, cam in enumerate(self.cams):
            for i, p in enumerate(self.points):
                q = K @ (p + np.asarray(cam['t']))
                self.obs.append([j, i, *list(q[:2]/q[2])])

    def test_reduce_error(self):
        noisy = self.points + np.array([.04, -.03, .07])
        r = ajustar(self.cams, self.obs, noisy, max_nfev=70)
        self.assertLess(r['rms_final_px'], r['rms_inicial_px'])
        self.assertLess(r['rms_final_px'], 0.05)

    def test_preserva_anclas(self):
        r = ajustar(self.cams, self.obs, self.points, max_nfev=10)
        self.assertEqual(r['camaras'][0]['t'], self.cams[0]['t'])
        self.assertEqual(r['camaras'][1]['t'], self.cams[1]['t'])

    def test_indices_invalidos(self):
        bad = [list(row) for row in self.obs]
        bad[0][1] = 999
        with self.assertRaises(ValueError):
            ajustar(self.cams, bad, self.points)

    def test_camaras_insuficientes(self):
        with self.assertRaises(ValueError):
            ajustar(self.cams[:1], self.obs, self.points)
