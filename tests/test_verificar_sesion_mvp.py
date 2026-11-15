"""Prueba de reutilización de resultados COLMAP existentes."""
import tempfile
import unittest
from pathlib import Path

from tools.verificar_sesion_mvp import verificar_sesion


class VerificarSesionTests(unittest.TestCase):
    def test_detecta_nube_sin_reconstruir(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            salida = raiz / "colmap"
            salida.mkdir()
            nube = salida / "modelo_000.ply"
            nube.write_text(
                "ply\nformat ascii 1.0\nelement vertex 4\n"
                "property float x\nproperty float y\nproperty float z\n"
                "end_header\n0 0 0\n1 0 0\n0 1 0\n0 0 1\n",
                encoding="ascii",
            )
            (raiz / "malla.obj").write_text("v 0 0 0\n", encoding="utf-8")
            reporte = verificar_sesion(raiz)
            self.assertEqual(reporte["reutilizar_nube"], str(nube))
            self.assertEqual(reporte["nubes_validas_por_cabecera"][0]["puntos_declarados"], 4)
            self.assertEqual(len(reporte["archivos_obj"]), 1)

    def test_sesion_sin_nube(self):
        with tempfile.TemporaryDirectory() as tmp:
            reporte = verificar_sesion(tmp)
            self.assertIsNone(reporte["reutilizar_nube"])


if __name__ == "__main__":
    unittest.main()
