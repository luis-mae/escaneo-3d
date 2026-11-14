import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np

from tools.fotos_a_nube_global import fotos_a_nube
from tools.leer_ply import leer_ply_xyz


class TestFotosANubeGlobal(unittest.TestCase):
    def crear_fotos(self, raiz, tamanos=((64, 80), (64, 80))):
        rutas = []
        for i, (h, w) in enumerate(tamanos):
            ruta = raiz / f"foto{i}.png"
            cv2.imwrite(str(ruta), np.zeros((h, w), dtype=np.uint8))
            rutas.append(ruta)
        return rutas

    def test_exporta_nube_e_integridad(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            fotos = self.crear_fotos(raiz)
            salida = raiz / "salida"
            puntos = [[float(i), float(i % 3), float(i % 4)] for i in range(12)]
            tracks = {"puntos_por_imagen": {}, "tracks": [], "pares": []}
            sfm = {"estado": "sfm_incremental_experimental", "puntos": puntos,
                   "puntos_3d": 12, "camaras": {}, "vistas": [], "escala": "arbitraria"}
            with patch("tools.fotos_a_nube_global.extraer_tracks", return_value=tracks), \
                 patch("tools.fotos_a_nube_global.reconstruir_tracks", return_value=sfm):
                informe = fotos_a_nube(fotos, 700, salida)
            self.assertEqual(len(leer_ply_xyz(salida / "nube.ply")), 12)
            self.assertEqual(informe["sha256_ply"],
                             hashlib.sha256((salida / "nube.ply").read_bytes()).hexdigest())
            self.assertEqual(informe["sha256_tracks"],
                             hashlib.sha256((salida / "tracks.json").read_bytes()).hexdigest())
            self.assertEqual(json.loads((salida / "informe.json").read_text())["ancho"], 80)

    def test_rechaza_resoluciones_distintas(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            fotos = self.crear_fotos(raiz, ((64, 80), (80, 64)))
            with self.assertRaisesRegex(ValueError, "misma resolución"):
                fotos_a_nube(fotos, 700, raiz / "salida")

    def test_rechaza_fotos_duplicadas(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            fotos = self.crear_fotos(raiz)
            with self.assertRaisesRegex(ValueError, "distintas"):
                fotos_a_nube([fotos[0], fotos[0]], 700, raiz / "salida")

    def test_no_pisa_archivos(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            fotos = self.crear_fotos(raiz)
            salida = raiz / "salida"
            salida.mkdir()
            (salida / "nube.ply").write_text("conservar")
            with self.assertRaises(FileExistsError):
                fotos_a_nube(fotos, 700, salida)
            self.assertEqual((salida / "nube.ply").read_text(), "conservar")
