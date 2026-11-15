"""Integración: COLMAP simulado con nube real, mallado y exportadores reales."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.escanear_fotos_mvp import escanear_fotos_mvp


class IntegracionFotosMvpTests(unittest.TestCase):
    def test_fotos_a_stl_con_nube_sintetica(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            fotos = raiz / "fotos"
            fotos.mkdir()
            salida = raiz / "resultado"

            def colmap_simulado(fotos_dir, destino, **kwargs):
                destino.mkdir(parents=True)
                nube = destino / "modelo_000.ply"
                puntos = [(0, 0, 0), (1, 0, 0), (0, 1, 0),
                          (0, 0, 1), (.2, .2, .2), (.3, .1, .1)]
                with nube.open("w", encoding="ascii") as archivo:
                    archivo.write("ply\nformat ascii 1.0\nelement vertex 6\n")
                    archivo.write("property float x\nproperty float y\n")
                    archivo.write("property float z\nend_header\n")
                    for x, y, z in puntos:
                        archivo.write(f"{x} {y} {z}\n")
                return {"modelos_dispersos": ["sparse/0"],
                        "exportaciones_ply": [{"exportado": True, "ply": nube.name}]}

            with patch("tools.escanear_fotos_mvp.ejecutar_colmap",
                       side_effect=colmap_simulado):
                resultado = escanear_fotos_mvp(fotos, salida, alpha=5)
            self.assertEqual(resultado["modelos_reconstruidos"], 1)
            for formato in ("obj", "stl", "glb"):
                self.assertGreater(Path(resultado["archivos"][formato]).stat().st_size, 0)
            self.assertTrue((salida / "resultado_mvp.json").is_file())
            self.assertTrue((salida / "modelo_3d" / "resumen_mvp.json").is_file())


if __name__ == "__main__":
    unittest.main()
