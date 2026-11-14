import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tools.colmap_denso import densificar_colmap


class TestColmapDenso(unittest.TestCase):
    def preparar(self, raiz):
        fotos = raiz / "fotos"
        fotos.mkdir()
        (fotos / "01.jpg").write_bytes(b"foto")
        resultado = raiz / "resultado"
        sparse = resultado / "sparse" / "0"
        sparse.mkdir(parents=True)
        for nombre in ("cameras.bin", "images.bin", "points3D.bin"):
            (sparse / nombre).write_bytes(b"datos")
        return resultado, fotos

    def test_tres_pasos_y_salida(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            resultado, fotos = self.preparar(raiz)
            llamadas = []
            def ejecutar(comando, **kwargs):
                llamadas.append(comando[1])
                if comando[1] == "stereo_fusion":
                    Path(comando[comando.index("--output_path") + 1]).write_bytes(b"ply\n")
                return SimpleNamespace(returncode=0, stderr="", stdout="")
            with patch("tools.colmap_denso.shutil.which", return_value="/usr/bin/colmap"), \
                 patch("tools.colmap_denso.subprocess.run", side_effect=ejecutar):
                informe = densificar_colmap(resultado, fotos)
            self.assertEqual(llamadas, ["image_undistorter", "patch_match_stereo", "stereo_fusion"])
            self.assertEqual(informe["estado"], "completado")
            self.assertTrue((resultado / "dense_0" / "informe_denso.json").exists())

    def test_error_interrumpe_y_conserva_informe(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            resultado, fotos = self.preparar(raiz)
            with patch("tools.colmap_denso.shutil.which", return_value="/usr/bin/colmap"), \
                 patch("tools.colmap_denso.subprocess.run",
                       return_value=SimpleNamespace(returncode=2, stderr="fallo", stdout="")):
                with self.assertRaises(RuntimeError):
                    densificar_colmap(resultado, fotos)
            self.assertTrue((resultado / "dense_0" / "informe_denso.json").exists())

    def test_rechaza_modelo_incompleto(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            resultado, fotos = self.preparar(raiz)
            (resultado / "sparse" / "0" / "points3D.bin").unlink()
            with self.assertRaisesRegex(ValueError, "incompleto"):
                densificar_colmap(resultado, fotos)


if __name__ == "__main__":
    unittest.main()
