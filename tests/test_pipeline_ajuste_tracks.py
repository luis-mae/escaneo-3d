import unittest
import numpy as np
from tools.pipeline_ajuste_tracks import reconstruir_y_ajustar

class TestPipelineAjusteTracks(unittest.TestCase):
    def setUp(self):
        K = [[600, 0, 320], [0, 600, 240], [0, 0, 1]]
        self.cams = {str(i): {'K': K, 'R': np.eye(3).tolist(), 't': [-i*.4, 0, 0]} for i in range(3)}
        self.pts = [[x, y, 4+.2*x] for x in (-.5, 0, .5) for y in (-.3, .3)]
        self.im = {}
        for name, cam in self.cams.items():
            self.im[name] = []
            for p in self.pts:
                q = np.asarray(K) @ (np.asarray(p)+np.asarray(cam['t']))
                self.im[name].append((q[:2]/q[2]).tolist())
        self.tracks = [{name: i for name in self.cams} for i in range(len(self.pts))]

    def test_integracion(self):
        r = reconstruir_y_ajustar(self.cams, self.im, self.tracks, max_nfev=20)
        self.assertEqual(len(r['puntos']), 6)
        self.assertLess(r['rms_final_px'], .01)
        self.assertEqual(r['camaras_ordenadas'], ['0','1','2'])

    def test_descarta_track_invalido(self):
        self.tracks.append({'0': 999, '1': 999})
        r = reconstruir_y_ajustar(self.cams, self.im, self.tracks, max_nfev=20)
        self.assertEqual(r['tracks_rechazados'], 1)

    def test_sin_puntos_suficientes(self):
        with self.assertRaises(ValueError):
            reconstruir_y_ajustar(self.cams, self.im, self.tracks[:2])
