"""Prueba del modo reanudar: no recalcula COLMAP ni modifica la sesión."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.escanear_fotos_mvp import reanudar_sesion_mvp


class ReanudarSesionMvpTests(unittest.TestCase):
    def test_reutiliza_nube_sin_ejecutar_colmap(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            sesion = raiz / "sesion"
            sesion.mkdir()
            nube = sesion / "modelo_000.ply"
            nube.write_text(
                "ply\nformat ascii 1.0\nelement vertex 6\n"
                "property float x\nproperty float y\nproperty float z\n"
                "end_header\n0 0 0\n1 0 0\n0 1 0\n0 0 1\n"
                "0.2 0.2 0.2\n0.3 0.1 0.1\n",
                encoding="ascii",
            )
            salida = raiz / "nuevo"
            with patch("tools.escanear_fotos_mvp.ejecutar_colmap") as colmap:
                reporte = reanudar_sesion_mvp(sesion, salida, alpha=5)
            colmap.assert_not_called()
            self.assertEqual(reporte["modo"], "reanudar_sin_colmap")
            for formato in ("obj", "stl", "glb"):
                self.assertGreater(Path(reporte["archivos"][formato]).stat().st_size, 0)
            self.assertTrue(nube.exists())
            with self.assertRaises(FileExistsError):
                reanudar_sesion_mvp(sesion, salida, alpha=5)

    def test_sin_nube(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            sesion = raiz / "sesion"
            sesion.mkdir()
            with self.assertRaisesRegex(ValueError, "PLY"):
                reanudar_sesion_mvp(sesion, raiz / "salida")


if __name__ == "__main__":
    unittest.main()
