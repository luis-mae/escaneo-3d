"""Pruebas de orquestación fotos -> COLMAP -> exportación sin instalar COLMAP."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.escanear_fotos_mvp import escanear_fotos_mvp


class EscanearFotosMvpTests(unittest.TestCase):
    def test_orquesta_fotos_nube_y_exportacion(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            fotos = raiz / "fotos"
            fotos.mkdir()
            salida = raiz / "resultado"

            def colmap_mock(fotos_dir, destino, **kwargs):
                destino.mkdir(parents=True)
                (destino / "modelo_000.ply").write_text(
                    "ply\nformat ascii 1.0\nelement vertex 4\n"
                    "property float x\nproperty float y\nproperty float z\n"
                    "end_header\n0 0 0\n1 0 0\n0 1 0\n0 0 1\n",
                    encoding="ascii",
                )
                return {
                    "modelos_dispersos": ["sparse/0"],
                    "exportaciones_ply": [{"exportado": True, "ply": "modelo_000.ply"}],
                }

            def malla_mock(nube, carpeta, **kwargs):
                self.assertTrue(nube.is_file())
                self.assertEqual(carpeta, salida / "modelo_3d")
                return {"metodo_superficie": "alpha_shape"}

            with patch("tools.escanear_fotos_mvp.ejecutar_colmap",
                       side_effect=colmap_mock) as reconstruir, \
                 patch("tools.escanear_fotos_mvp.procesar_nube_mvp",
                       side_effect=malla_mock) as mallar:
                resultado = escanear_fotos_mvp(fotos, salida)
            reconstruir.assert_called_once()
            mallar.assert_called_once()
            self.assertEqual(resultado["modelos_reconstruidos"], 1)
            self.assertTrue((salida / "resultado_mvp.json").is_file())
            with self.assertRaises(FileExistsError):
                escanear_fotos_mvp(fotos, salida)

    def test_rechaza_salida_dentro_de_fotos(self):
        with tempfile.TemporaryDirectory() as tmp:
            fotos = Path(tmp) / "fotos"
            fotos.mkdir()
            with self.assertRaisesRegex(ValueError, "separada"):
                escanear_fotos_mvp(fotos, fotos / "salida")

    def test_error_sin_nube(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            fotos = raiz / "fotos"
            fotos.mkdir()
            with patch("tools.escanear_fotos_mvp.ejecutar_colmap",
                       return_value={"exportaciones_ply": []}):
                with self.assertRaisesRegex(RuntimeError, "nube PLY"):
                    escanear_fotos_mvp(fotos, raiz / "salida")


if __name__ == "__main__":
    unittest.main()
