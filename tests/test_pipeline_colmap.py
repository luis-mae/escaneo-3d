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
            (salida / "sparse" / "0").mkdir(parents=True)
            with patch("tools.pipeline_colmap.ejecutar_colmap",
                       return_value={"estado": "reconstruccion_dispersa", "modelos_dispersos": ["sparse/0"]}) as disperso, \
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
            (salida / "sparse" / "0").mkdir(parents=True)
            with patch("tools.pipeline_colmap.ejecutar_colmap",
                       return_value={"estado": "reconstruccion_dispersa", "modelos_dispersos": ["sparse/0"]}), \
                 patch("tools.pipeline_colmap.densificar_colmap",
                       side_effect=RuntimeError("CUDA no disponible")):
                resultado = pipeline_colmap(raiz / "fotos", salida, denso=True)
            self.assertIn("CUDA", resultado["error_denso"])
            self.assertTrue((salida / "pipeline_colmap.json").exists())

    def test_prioriza_modelo_con_mayor_nube_valida(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            salida = raiz / "salida"
            (salida / "sparse" / "0").mkdir(parents=True)
            (salida / "sparse" / "1").mkdir()
            informe = {"estado": "reconstruccion_dispersa",
                       "modelos_dispersos": ["sparse/0", "sparse/1"],
                       "exportaciones_ply": [
                           {"modelo": "sparse/0", "exportado": True, "vertices": 10},
                           {"modelo": "sparse/1", "exportado": True, "vertices": 300}]}
            with patch("tools.pipeline_colmap.ejecutar_colmap", return_value=informe), \
                 patch("tools.pipeline_colmap.densificar_colmap",
                       return_value={"estado": "completado"}) as denso:
                resultado = pipeline_colmap(raiz / "fotos", salida, denso=True)
            self.assertEqual(resultado["modelo_denso_elegido"], "1")
            self.assertEqual(denso.call_args.kwargs["modelo"], "1")

    def test_no_densifica_si_fallo_reconstruccion_dispersa(self):
        with tempfile.TemporaryDirectory() as d:
            salida = Path(d) / "salida"
            salida.mkdir()
            with patch("tools.pipeline_colmap.ejecutar_colmap",
                       return_value={"estado": "incompleto", "modelos_dispersos": []}), \
                 patch("tools.pipeline_colmap.densificar_colmap") as denso:
                resultado = pipeline_colmap(Path(d) / "fotos", salida, denso=True)
            denso.assert_not_called()
            self.assertIn("dispersa", resultado["error_denso"])
            self.assertTrue((salida / "pipeline_colmap.json").is_file())

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
