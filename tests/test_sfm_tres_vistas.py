"""Prueba determinista de integración SfM con tres cámaras y escena sintética."""
import unittest

import numpy as np

from tools.sfm_incremental import reconstruir_tracks


class TestSfmTresVistas(unittest.TestCase):
    def test_registra_tercera_camara_y_audita(self):
        rng = np.random.default_rng(2026)
        puntos = np.column_stack((
            rng.uniform(-1.5, 1.5, 150),
            rng.uniform(-1., 1., 150),
            rng.uniform(5., 9., 150)))
        K = np.array([[900., 0., 640.], [0., 900., 360.], [0., 0., 1.]])
        desplazamientos = {
            "vista_01": np.array([0., 0., 0.]),
            "vista_02": np.array([-1., 0., 0.]),
            "vista_03": np.array([-1.6, -0.2, 0.]),
        }
        imagenes = {}
        for nombre, t in desplazamientos.items():
            proyeccion = (K @ (puntos + t).T).T
            imagenes[nombre] = (proyeccion[:, :2] / proyeccion[:, 2:]).tolist()
        datos = {
            "puntos_por_imagen": imagenes,
            "tracks": [{nombre: i for nombre in desplazamientos} for i in range(len(puntos))],
        }
        resultado = reconstruir_tracks(datos, 900., 1280, 720, min_inliers=12)
        self.assertEqual(resultado["estado"], "sfm_incremental_experimental")
        self.assertEqual(len(resultado["camaras"]), 3)
        self.assertEqual(resultado["vistas"][2]["estado"], "pnp_aceptado")
        self.assertGreaterEqual(resultado["puntos_3d"], 12)
        self.assertLess(resultado["auditoria"]["rms_reproyeccion_px"], 3.0)
        self.assertEqual(resultado["escala"], "arbitraria")


if __name__ == "__main__":
    unittest.main()
