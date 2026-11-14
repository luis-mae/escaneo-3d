import json
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.fotos_a_modelo import reconstruir_y_exportar
from tools.leer_ply import leer_ply_xyz


class TestFotosAModelo(unittest.TestCase):
    def setUp(self):
        self.puntos = [[0., 0., 0.], [1., 0., 0.], [0., 1., 0.],
                       [0., 0., 1.], [1., 1., 1.], [2., 1., 1.],
                       [1., 2., 1.], [1., 1., 2.], [2., 2., 2.],
                       [2., 0., 1.], [0., 2., 1.], [1., 0., 2.]]

    def resultado(self):
        return {"estado": "experimental", "puntos": self.puntos,
                "aceptados": len(self.puntos), "rechazados": 0}

    def test_exporta_ply_y_reporte_sin_malla(self):
        with tempfile.TemporaryDirectory() as tmp:
            salida = Path(tmp) / "resultado"
            with patch("tools.fotos_a_modelo.reconstruir_par", return_value=self.resultado()):
                informe = reconstruir_y_exportar("a.jpg", "b.jpg", 900, salida)
            self.assertEqual(len(leer_ply_xyz(salida / "nube.ply")), 12)
            self.assertEqual(json.loads((salida / "informe.json").read_text())["escala"], "arbitraria")
            self.assertFalse((salida / "superficie.obj").exists())
            self.assertEqual(informe["aceptados"], 12)
            self.assertEqual(informe["archivos"]["nube.ply"],
                             hashlib.sha256((salida / "nube.ply").read_bytes()).hexdigest())

    def test_no_sobrescribe(self):
        with tempfile.TemporaryDirectory() as tmp:
            salida = Path(tmp)
            (salida / "nube.ply").write_text("protegido")
            with patch("tools.fotos_a_modelo.reconstruir_par", return_value=self.resultado()):
                with self.assertRaises(FileExistsError):
                    reconstruir_y_exportar("a.jpg", "b.jpg", 900, salida)
            self.assertEqual((salida / "nube.ply").read_text(), "protegido")

    def test_no_exporta_si_falla_reconstruccion(self):
        with tempfile.TemporaryDirectory() as tmp:
            salida = Path(tmp) / "resultado"
            with patch("tools.fotos_a_modelo.reconstruir_par",
                       return_value={"estado": "insuficiente", "motivo": "pocas coincidencias"}):
                with self.assertRaisesRegex(ValueError, "insuficiente"):
                    reconstruir_y_exportar("a.jpg", "b.jpg", 900, salida)
            self.assertFalse(salida.exists())

    def test_rechaza_minimo_invalido(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "min_puntos"):
                reconstruir_y_exportar("a.jpg", "b.jpg", 900, tmp, min_puntos=7)

    def test_rechaza_focal_invalida(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                reconstruir_y_exportar("a.jpg", "b.jpg", -1, tmp)
