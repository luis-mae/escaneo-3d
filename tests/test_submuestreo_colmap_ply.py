import tempfile
import unittest
from pathlib import Path

from tools.leer_colmap_ply import leer_nube_colmap_ply


class TestSubmuestreoColmapPLY(unittest.TestCase):
    def crear_ascii(self, ruta, cantidad=10):
        filas = "".join(f"{i} {i + 1} {i + 2}\n" for i in range(cantidad))
        ruta.write_text(
            "ply\nformat ascii 1.0\nelement vertex " + str(cantidad) +
            "\nproperty float x\nproperty float y\nproperty float z\nend_header\n" +
            filas, encoding="ascii"
        )

    def test_rechaza_exceso_sin_submuestreo(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "nube.ply"
            self.crear_ascii(ruta)
            with self.assertRaisesRegex(ValueError, "fuera del límite"):
                leer_nube_colmap_ply(ruta, max_puntos=4)

    def test_submuestreo_determinista_respeta_limite(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "nube.ply"
            self.crear_ascii(ruta)
            a = leer_nube_colmap_ply(ruta, max_puntos=4, submuestrear=True)
            b = leer_nube_colmap_ply(ruta, max_puntos=4, submuestrear=True)
            self.assertEqual(a.shape, (4, 3))
            self.assertEqual(a.tolist(), b.tolist())
            self.assertTrue((a[:, 0] >= 0).all())
            self.assertTrue((a[:, 0] < 10).all())
            self.assertEqual(len(set(a[:, 0].tolist())), 4)

    def test_no_submuestrea_si_ya_cabe(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "nube.ply"
            self.crear_ascii(ruta, 5)
            puntos = leer_nube_colmap_ply(ruta, max_puntos=10, submuestrear=True)
            self.assertEqual(puntos.shape, (5, 3))

    def test_rechaza_nan_incluso_en_punto_no_muestreado(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "nube.ply"
            filas = "".join(
                ("nan 0 0\\n" if i == 8 else f"{i} {i + 1} {i + 2}\\n")
                for i in range(10)
            )
            ruta.write_text(
                "ply\\nformat ascii 1.0\\nelement vertex 10\\n"
                "property float x\\nproperty float y\\nproperty float z\\n"
                "end_header\\n" + filas, encoding="ascii"
            )
            with self.assertRaisesRegex(ValueError, "no finitas"):
                leer_nube_colmap_ply(ruta, max_puntos=4, submuestrear=True)


if __name__ == "__main__":
    unittest.main()
