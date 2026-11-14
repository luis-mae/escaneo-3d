import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.pipeline_colmap import pipeline_colmap


class TestPipelineColmap(unittest.TestCase):
    def test_orquesta_fases_y_escribe_informe(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            salida = raiz / "salida"
            salida.mkdir()
            with patch("tools.pipeline_colmap.ejecutar_colmap",
                       return_value={"estado": "reconstruccion_dispersa"}) as disperso, \
                 patch("tools.pipeline_colmap.densificar_colmap",
                       return_value={"estado": "completado"}) as denso:
                resultado = pipeline_colmap(raiz / "fotos", salida, denso=True)
            disperso.assert_called_once()
            denso.assert_called_once()
            self.assertEqual(resultado["denso"]["estado"], "completado")
            self.assertEqual(json.loads((salida / "pipeline_colmap.json").read_text())["motor"],
                             "COLMAP")

    def test_fallo_denso_conserva_informe(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            salida = raiz / "salida"
            salida.mkdir()
            with patch("tools.pipeline_colmap.ejecutar_colmap",
                       return_value={"estado": "reconstruccion_dispersa"}), \
                 patch("tools.pipeline_colmap.densificar_colmap",
                       side_effect=RuntimeError("CUDA no disponible")):
                resultado = pipeline_colmap(raiz / "fotos", salida, denso=True)
            self.assertIn("CUDA", resultado["error_denso"])
            self.assertTrue((salida / "pipeline_colmap.json").exists())

    def test_solo_dispersa_no_llama_denso(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            salida = raiz / "salida"
            salida.mkdir()
            with patch("tools.pipeline_colmap.ejecutar_colmap",
                       return_value={"estado": "reconstruccion_dispersa"}), \
                 patch("tools.pipeline_colmap.densificar_colmap") as denso:
                resultado = pipeline_colmap(raiz / "fotos", salida)
            denso.assert_not_called()
            self.assertFalse(resultado["denso_solicitado"])


if __name__ == "__main__":
    unittest.main()
