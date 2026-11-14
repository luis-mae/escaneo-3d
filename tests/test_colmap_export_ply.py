import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, SimpleNamespace

from tools.motor_colmap import ejecutar_colmap


class TestColmapExportPly(unittest.TestCase):
    def test_pipeline_exporta_ply(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            fotos = raiz / "fotos"
            fotos.mkdir()
            (fotos / "a.jpg").write_bytes(b"foto")
            salida = raiz / "resultado"
            comandos = []

            def simular(comando, **kwargs):
                comandos.append(comando[1])
                if comando[1] == "mapper":
                    modelo = salida / "sparse" / "0"
                    modelo.mkdir()
                    for nombre in ("cameras.bin", "images.bin", "points3D.bin"):
                        (modelo / nombre).write_bytes(b"demo")
                if comando[1] == "model_converter":
                    Path(comando[comando.index("--output_path") + 1]).write_bytes(
                        b"ply\\nformat ascii 1.0\\nelement vertex 0\\nend_header\\n")
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            with patch("tools.motor_colmap.shutil.which", return_value="/usr/bin/colmap"), \
                 patch("tools.motor_colmap.subprocess.run", side_effect=simular):
                informe = ejecutar_colmap(fotos, salida)
            self.assertEqual(informe["estado"], "reconstruccion_dispersa")
            self.assertEqual(comandos, ["feature_extractor", "exhaustive_matcher",
                                        "mapper", "model_converter"])
            self.assertTrue((salida / "modelo_000.ply").exists())
            self.assertTrue(json.loads((salida / "informe_colmap.json").read_text())
                            ["exportaciones_ply"][0]["exportado"])

    def test_falla_exportacion_sin_ply(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            fotos = raiz / "fotos"
            fotos.mkdir()
            (fotos / "a.jpg").write_bytes(b"foto")
            salida = raiz / "resultado"

            def simular(comando, **kwargs):
                if comando[1] == "mapper":
                    modelo = salida / "sparse" / "0"
                    modelo.mkdir()
                    for nombre in ("cameras.bin", "images.bin", "points3D.bin"):
                        (modelo / nombre).write_bytes(b"demo")
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            with patch("tools.motor_colmap.shutil.which", return_value="/usr/bin/colmap"), \
                 patch("tools.motor_colmap.subprocess.run", side_effect=simular):
                with self.assertRaises(RuntimeError):
                    ejecutar_colmap(fotos, salida)
            self.assertEqual(json.loads((salida / "informe_colmap.json").read_text())
                             ["estado"], "exportacion_incompleta")


if __name__ == "__main__":
    unittest.main()
