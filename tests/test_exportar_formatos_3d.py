import tempfile
import unittest
from pathlib import Path

from tools.exportar_formatos_3d import exportar_formatos
from tools.verificar_stl import analizar


class TestExportarFormatos3D(unittest.TestCase):
    def test_exporta_tres_formatos(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            entrada = raiz / "malla.obj"
            entrada.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 0 1\n"
                               "f 1 3 2\nf 1 2 4\nf 1 4 3\nf 2 3 4\n")
            salida = raiz / "exportacion"
            informe = exportar_formatos(entrada, salida)
            self.assertEqual(len(informe["archivos"]), 3)
            self.assertEqual(analizar(salida / "modelo.stl")["triangulos"], 4)
            self.assertIn("element face 4", (salida / "modelo.ply").read_text())
            self.assertTrue((salida / "modelo.obj").exists())
            self.assertTrue((salida / "informe_exportacion.json").exists())

    def test_no_sobrescribe(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            entrada = raiz / "malla.obj"
            entrada.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
            salida = raiz / "salida"
            salida.mkdir()
            with self.assertRaises(FileExistsError):
                exportar_formatos(entrada, salida)

    def test_rechaza_formato_desconocido(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            entrada = raiz / "malla.obj"
            entrada.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
            with self.assertRaises(ValueError):
                exportar_formatos(entrada, raiz / "salida", ("exe",))

    def test_fallo_intermedio_limpia_exportacion_parcial(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            entrada = raiz / "malla.obj"
            entrada.write_text(
                "v 0 0 0\nv 1 0 0\nv 2 0 0\nf 1 2 3\n",
                encoding="utf-8",
            )
            salida = raiz / "exportacion"
            with self.assertRaisesRegex(ValueError, "degenerada"):
                exportar_formatos(entrada, salida)
            self.assertFalse(salida.exists())


if __name__ == "__main__":
    unittest.main()
