"""Pruebas de integración lógica del pipeline, sin instalar COLMAP."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.pipeline_colmap import pipeline_colmap


class PipelineColmapTests(unittest.TestCase):
    def test_elige_modelo_existente_si_no_hay_cero(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            fotos = raiz / "fotos"
            fotos.mkdir()
            salida = raiz / "resultado"
            (salida / "sparse" / "2").mkdir(parents=True)
            informe = {"estado": "reconstruccion_dispersa",
                       "modelos_dispersos": ["sparse/2"]}
            with patch("tools.pipeline_colmap.ejecutar_colmap", return_value=informe), \
                 patch("tools.pipeline_colmap.densificar_colmap", return_value={"estado": "completado"}) as denso:
                resultado = pipeline_colmap(fotos, salida, denso=True)
            self.assertEqual(resultado["modelo_denso_elegido"], "2")
            self.assertEqual(denso.call_args.kwargs["modelo"], "2")
            self.assertTrue((salida / "pipeline_colmap.json").is_file())

    def test_prioriza_modelo_con_ply_exportado(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            fotos = raiz / "fotos"
            fotos.mkdir()
            salida = raiz / "resultado"
            (salida / "sparse" / "0").mkdir(parents=True)
            (salida / "sparse" / "1").mkdir(parents=True)
            informe = {"estado": "reconstruccion_dispersa",
                       "modelos_dispersos": ["sparse/0", "sparse/1"],
                       "exportaciones_ply": [
                           {"modelo": "sparse/0", "exportado": False},
                           {"modelo": "sparse/1", "exportado": True}]}
            with patch("tools.pipeline_colmap.ejecutar_colmap", return_value=informe), \
                 patch("tools.pipeline_colmap.densificar_colmap", return_value={"estado": "completado"}) as denso:
                resultado = pipeline_colmap(fotos, salida, denso=True)
            self.assertEqual(resultado["modelo_denso_elegido"], "1")
            self.assertEqual(denso.call_args.kwargs["modelo"], "1")

    def test_error_denso_no_pierde_resultado_disperso(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            fotos = raiz / "fotos"
            fotos.mkdir()
            salida = raiz / "resultado"
            (salida / "sparse" / "0").mkdir(parents=True)
            informe = {"estado": "reconstruccion_dispersa",
                       "modelos_dispersos": ["sparse/0"]}
            with patch("tools.pipeline_colmap.ejecutar_colmap", return_value=informe), \
                 patch("tools.pipeline_colmap.densificar_colmap", side_effect=RuntimeError("sin GPU")):
                resultado = pipeline_colmap(fotos, salida, denso=True)
            self.assertEqual(resultado["error_denso"], "sin GPU")
            self.assertEqual(resultado["disperso"], informe)
            self.assertTrue((salida / "pipeline_colmap.json").exists())

    def test_rechaza_timeout_invalido(self):
        with self.assertRaises(ValueError):
            pipeline_colmap("fotos", "salida", timeout_segundos=0)


if __name__ == "__main__":
    unittest.main()
