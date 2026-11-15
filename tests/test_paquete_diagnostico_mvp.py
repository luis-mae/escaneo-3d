"""Pruebas del ZIP diagnóstico: sin fotos ni nube completa."""
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.paquete_diagnostico_mvp import generar_diagnostico


class PaqueteDiagnosticoTests(unittest.TestCase):
    def test_zip_no_contiene_fotos_ni_coordenadas(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            sesion = raiz / "sesion"
            sesion.mkdir()
            (sesion / "privado.jpg").write_bytes(b"FOTO-PRIVADA")
            (sesion / "modelo_000.ply").write_text(
                "ply\nformat ascii 1.0\nelement vertex 4\n"
                "property float x\nproperty float y\nproperty float z\n"
                "end_header\n100 200 300\n101 200 300\n"
                "100 201 300\n100 200 301\n",
                encoding="ascii",
            )
            destino = raiz / "diagnostico.zip"
            generar_diagnostico(sesion, destino)
            with zipfile.ZipFile(destino) as z:
                self.assertEqual(set(z.namelist()), {
                    "diagnostico.json", "cabeceras_ply.json", "LEEME.txt",
                })
                contenido = b"".join(z.read(x) for x in z.namelist())
                self.assertNotIn(b"FOTO-PRIVADA", contenido)
                self.assertNotIn(b"100 200 300", contenido)
                self.assertNotIn(str(sesion).encode(), contenido)
                reporte = json.loads(z.read("diagnostico.json"))
                self.assertGreaterEqual(reporte["ply_detectados"], 1)

    def test_no_sobrescribe_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            sesion = raiz / "sesion"
            sesion.mkdir()
            destino = raiz / "diagnostico.zip"
            destino.write_bytes(b"existente")
            with self.assertRaises(FileExistsError):
                generar_diagnostico(sesion, destino)
            self.assertEqual(destino.read_bytes(), b"existente")


if __name__ == "__main__":
    unittest.main()
