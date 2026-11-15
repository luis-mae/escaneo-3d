"""Pruebas del procesador por lotes sin descargar modelos de IA."""
import tempfile
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from tools.quitar_fondo import process_folder


class QuitarFondoCLITests(unittest.TestCase):
    def test_generar_png_transparente_y_mascara(self):
        with tempfile.TemporaryDirectory() as temporal:
            base = Path(temporal)
            fotos = base / "fotos"
            fotos.mkdir()
            Image.new("RGB", (8, 8), "red").save(fotos / "objeto.jpg")
            def simular_remove(imagen, session=None):
                rgba = imagen.convert("RGBA")
                rgba.putalpha(Image.new("L", imagen.size, 100))
                return rgba
            import sys
            from types import SimpleNamespace
            falso = SimpleNamespace(new_session=lambda nombre: object(), remove=simular_remove)
            with patch.dict(sys.modules, {"rembg": falso}):
                cantidad = process_folder(fotos, base / "rgb", base / "mascaras",
                                          transparent=base / "transparentes")
            self.assertEqual(cantidad, 1)
            with Image.open(base / "transparentes" / "0001.png") as resultado:
                self.assertEqual(resultado.mode, "RGBA")
                self.assertEqual(resultado.getpixel((0, 0))[3], 100)
            with Image.open(base / "mascaras" / "0001.png.png") as mascara:
                self.assertEqual(mascara.getpixel((0, 0)), 0)
            self.assertTrue((base / "rgb" / "0001.png").is_file())
            mapa = json.loads((base / "rgb" / "origenes.json").read_text(encoding="utf-8"))
            self.assertEqual(mapa[0]["original"], "objeto.jpg")
            self.assertEqual(mapa[0]["transparente"], "0001.png")

    def test_no_sobrescribe_salida_preexistente(self):
        with tempfile.TemporaryDirectory() as temporal:
            base = Path(temporal)
            fotos = base / "fotos"
            fotos.mkdir()
            Image.new("RGB", (4, 4), "blue").save(fotos / "foto.png")
            (base / "rgb").mkdir()
            import sys
            from types import SimpleNamespace
            falso = SimpleNamespace(new_session=lambda nombre: object(), remove=lambda image, session=None: image)
            with patch.dict(sys.modules, {"rembg": falso}):
                with self.assertRaises(FileExistsError):
                    process_folder(fotos, base / "rgb", base / "mascaras")


if __name__ == "__main__":
    unittest.main()
