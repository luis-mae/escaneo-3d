"""Pruebas de reconstrucción dispersa con ejecutable COLMAP simulado."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.motor_colmap import ejecutar_colmap


class MotorColmapTests(unittest.TestCase):
    def test_reconstruye_y_exporta_nube(self):
        with tempfile.TemporaryDirectory() as temporal:
            raiz = Path(temporal)
            fotos = raiz / "fotos"
            fotos.mkdir()
            (fotos / "foto.jpg").write_bytes(b"imagen")
            salida = raiz / "resultado"
            def simular(comando, *args, **kwargs):
                paso = comando[1]
                if paso == "mapper":
                    modelo = salida / "sparse" / "0"
                    modelo.mkdir()
                    for nombre in ("cameras.bin", "images.bin", "points3D.bin"):
                        (modelo / nombre).write_bytes(b"datos")
                if paso == "model_converter":
                    Path(comando[comando.index("--output_path") + 1]).write_bytes(b"ply\nend_header\n")
                return subprocess.CompletedProcess(comando, 0, "", "")
            with patch("tools.motor_colmap.shutil.which", return_value="/usr/bin/colmap"), \
                 patch("tools.motor_colmap.ejecutar_comando", side_effect=simular):
                resultado = ejecutar_colmap(fotos, salida)
            self.assertEqual(resultado["estado"], "reconstruccion_dispersa")
            self.assertTrue(resultado["exportaciones_ply"][0]["exportado"])
            self.assertTrue((salida / "modelo_000.ply").is_file())

    def test_elimina_nube_parcial_de_exportacion_fallida(self):
        with tempfile.TemporaryDirectory() as temporal:
            raiz = Path(temporal)
            fotos = raiz / "fotos"
            fotos.mkdir()
            (fotos / "foto.jpg").write_bytes(b"imagen")
            salida = raiz / "resultado"
            def simular(comando, *args, **kwargs):
                if comando[1] == "mapper":
                    modelo = salida / "sparse" / "0"
                    modelo.mkdir()
                    for nombre in ("cameras.bin", "images.bin", "points3D.bin"):
                        (modelo / nombre).write_bytes(b"datos")
                if comando[1] == "model_converter":
                    Path(comando[comando.index("--output_path") + 1]).write_bytes(b"parcial")
                    return subprocess.CompletedProcess(comando, 1, "", "falló")
                return subprocess.CompletedProcess(comando, 0, "", "")
            with patch("tools.motor_colmap.shutil.which", return_value="/usr/bin/colmap"), \
                 patch("tools.motor_colmap.ejecutar_comando", side_effect=simular):
                with self.assertRaises(RuntimeError):
                    ejecutar_colmap(fotos, salida)
            self.assertFalse((salida / "modelo_000.ply").exists())
            self.assertTrue((salida / "informe_colmap.json").is_file())


if __name__ == "__main__":
    unittest.main()
