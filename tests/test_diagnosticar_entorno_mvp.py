"""Pruebas de diagnóstico previo sin requerir COLMAP instalado."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.diagnosticar_entorno_mvp import diagnosticar_entorno


class DiagnosticarEntornoTests(unittest.TestCase):
    def test_sesion_sin_ply_no_esta_lista(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("tools.diagnosticar_entorno_mvp.importlib.util.find_spec", return_value=object()):
                reporte = diagnosticar_entorno(tmp)
            self.assertFalse(reporte["listo_para_reanudar"])
            self.assertEqual(reporte["sesion"]["ply_detectados"], 0)

    def test_detecta_dependencias_faltantes(self):
        with patch("tools.diagnosticar_entorno_mvp.importlib.util.find_spec", return_value=None):
            reporte = diagnosticar_entorno()
        self.assertFalse(reporte["puede_procesar_ply"])
        self.assertFalse(reporte["listo_para_reanudar"])

    def test_detecta_sesion_inexistente(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "no_existe"
            with patch("tools.diagnosticar_entorno_mvp.importlib.util.find_spec", return_value=object()):
                reporte = diagnosticar_entorno(ruta)
            self.assertFalse(reporte["listo_para_reanudar"])
            self.assertIn("Sesión inaccesible", reporte["problemas"][0])


if __name__ == "__main__":
    unittest.main()
