import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, SimpleNamespace

from tools.exportar_colmap_ply import exportar_modelos_colmap


class TestExportarColmapPly(unittest.TestCase):
    def crear_modelo(self, raiz):
        modelo = raiz / "sparse" / "0"
        modelo.mkdir(parents=True)
        for nombre in ("cameras.bin", "images.bin", "points3D.bin"):
            (modelo / nombre).write_bytes(b"datos")
        return modelo

    def test_exportacion_correcta(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            self.crear_modelo(raiz)
            def ejecutar(comando, **kwargs):
                Path(comando[comando.index("--output_path") + 1]).write_bytes(b"ply\n")
                return SimpleNamespace(returncode=0, stderr="", stdout="")
            with patch("tools.exportar_colmap_ply.shutil.which", return_value="/usr/bin/colmap"), \
                 patch("tools.exportar_colmap_ply.subprocess.run", side_effect=ejecutar):
                resultado = exportar_modelos_colmap(raiz)
            self.assertEqual(resultado["exportaciones"][0]["estado"], "exportado")
            self.assertTrue((raiz / "modelo_0.ply").exists())

    def test_no_sobrescribe_exportacion(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            self.crear_modelo(raiz)
            (raiz / "modelo_0.ply").write_bytes(b"original")
            with patch("tools.exportar_colmap_ply.shutil.which", return_value="/usr/bin/colmap"), \
                 patch("tools.exportar_colmap_ply.subprocess.run") as ejecutar:
                resultado = exportar_modelos_colmap(raiz)
            ejecutar.assert_not_called()
            self.assertEqual(resultado["exportaciones"][0]["estado"], "ya_existe")
            self.assertEqual((raiz / "modelo_0.ply").read_bytes(), b"original")

    def test_rechaza_modelo_incompleto(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            (raiz / "sparse").mkdir()
            with patch("tools.exportar_colmap_ply.shutil.which", return_value="/usr/bin/colmap"):
                with self.assertRaises(ValueError):
                    exportar_modelos_colmap(raiz)


if __name__ == "__main__":
    unittest.main()
