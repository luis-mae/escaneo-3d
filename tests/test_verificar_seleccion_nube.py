"""Regresiones: no confundir una malla exportada con una nube COLMAP."""
import tempfile
import unittest
from pathlib import Path

from tools.verificar_sesion_mvp import verificar_sesion


def ply(path, cantidad):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "ply\nformat ascii 1.0\nelement vertex %d\n"
        "property float x\nproperty float y\nproperty float z\n"
        "end_header\n" % cantidad + "0 0 0\n" * cantidad,
        encoding="ascii",
    )


class SeleccionNubeTests(unittest.TestCase):
    def test_prioriza_fused_sobre_sparse(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            ply(base / "modelo_000.ply", 40)
            ply(base / "dense" / "fused.ply", 12)
            reporte = verificar_sesion(base)
            self.assertEqual(Path(reporte["reutilizar_nube"]).name, "fused.ply")
            self.assertEqual(reporte["clasificacion_nube"], "densa_por_nombre_sin_validar")

    def test_no_recicla_exportacion(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            ply(base / "modelo_3d" / "exportados" / "modelo.ply", 200)
            reporte = verificar_sesion(base)
            self.assertIsNone(reporte["reutilizar_nube"])
            self.assertEqual(reporte["clasificacion_nube"], "sin_nube")

    def test_prefiere_sparse_frente_a_malla(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            ply(base / "modelo_000.ply", 10)
            ply(base / "modelo_3d" / "exportados" / "modelo.ply", 100)
            reporte = verificar_sesion(base)
            self.assertEqual(Path(reporte["reutilizar_nube"]).name, "modelo_000.ply")


if __name__ == "__main__":
    unittest.main()
