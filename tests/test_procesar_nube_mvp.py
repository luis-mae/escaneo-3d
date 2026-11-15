"""Smoke test del procesamiento local en un solo comando."""
import tempfile
import unittest
from pathlib import Path

from tools.procesar_nube_mvp import procesar_nube_mvp


class ProcesarNubeMvpTests(unittest.TestCase):
    def test_pipeline_exporta_obj_stl_glb(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            nube = raiz / "entrada.ply"
            puntos = [(0, 0, 0), (1, 0, 0), (0, 1, 0),
                      (0, 0, 1), (.2, .2, .2), (.3, .2, .1)]
            with nube.open("w", encoding="ascii") as archivo:
                archivo.write("ply\nformat ascii 1.0\nelement vertex 6\n")
                archivo.write("property float x\nproperty float y\nproperty float z\nend_header\n")
                for p in puntos:
                    archivo.write(f"{p[0]} {p[1]} {p[2]}\n")
            salida = raiz / "salida"
            informe = procesar_nube_mvp(nube, salida, alpha=5)
            self.assertEqual(informe["metodo_superficie"], "alpha_shape")
            self.assertTrue(informe["auditoria_formatos"]["exportaciones_validas_basicas"])
            self.assertIn("malla_cerrada_por_aristas", informe["control_calidad"])
            self.assertFalse(informe["control_calidad"]["apto_para_impresion"])
            for extension in ("obj", "stl", "glb"):
                self.assertGreater((salida / "exportados" / ("modelo." + extension)).stat().st_size, 0)
            self.assertTrue((salida / "resumen_mvp.json").exists())
            with self.assertRaises(FileExistsError):
                procesar_nube_mvp(nube, salida, alpha=5)


if __name__ == "__main__":
    unittest.main()
