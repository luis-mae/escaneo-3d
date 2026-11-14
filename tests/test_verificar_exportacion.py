import json
import tempfile
import unittest
from pathlib import Path
from tools.verificar_exportacion import verificar_exportacion


class TestVerificarExportacion(unittest.TestCase):
    def crear(self, carpeta, cantidad=2, filas="0 0 0\n1 0 0\n"):
        (carpeta / "informe_controlado.json").write_text(json.dumps({
            "estado": "fusion_rigida_controlada_experimental", "puntos_salida": cantidad
        }), encoding="utf-8")
        (carpeta / "fusion_controlada.ply").write_text(
            "ply\nformat ascii 1.0\nelement vertex 2\n"
            "property float x\nproperty float y\nproperty float z\nend_header\n" + filas,
            encoding="ascii")

    def test_integridad(self):
        with tempfile.TemporaryDirectory() as tmp:
            carpeta = Path(tmp)
            self.crear(carpeta)
            r = verificar_exportacion(carpeta)
            self.assertEqual(r["vertices"], 2)
            self.assertEqual(len(r["sha256_ply"]), 64)

    def test_cantidad_informe_distinta(self):
        with tempfile.TemporaryDirectory() as tmp:
            carpeta = Path(tmp)
            self.crear(carpeta, cantidad=3)
            with self.assertRaisesRegex(ValueError, "no coincide"):
                verificar_exportacion(carpeta)

    def test_ply_truncado(self):
        with tempfile.TemporaryDirectory() as tmp:
            carpeta = Path(tmp)
            self.crear(carpeta, filas="0 0 0\n")
            with self.assertRaisesRegex(ValueError, "truncados"):
                verificar_exportacion(carpeta)

    def test_ply_no_finito(self):
        with tempfile.TemporaryDirectory() as tmp:
            carpeta = Path(tmp)
            self.crear(carpeta, filas="0 0 0\nnan 0 0\n")
            with self.assertRaisesRegex(ValueError, "no finitas"):
                verificar_exportacion(carpeta)

    def test_manifiesto_detecta_modificacion(self):
        from tools.verificar_exportacion import sha256
        with tempfile.TemporaryDirectory() as tmp:
            carpeta = Path(tmp)
            self.crear(carpeta)
            archivos = {nombre: sha256(carpeta / nombre) for nombre in
                        ("fusion_controlada.ply", "informe_controlado.json")}
            (carpeta / "manifiesto_sha256.json").write_text(json.dumps({
                "algoritmo": "sha256", "archivos": archivos
            }), encoding="utf-8")
            verificar_exportacion(carpeta)
            (carpeta / "fusion_controlada.ply").write_text(
                (carpeta / "fusion_controlada.ply").read_text() + "2 0 0\\n")
            with self.assertRaises(ValueError):
                verificar_exportacion(carpeta)

    def test_archivos_ausentes(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "Faltan"):
                verificar_exportacion(tmp)


if __name__ == "__main__":
    unittest.main()
