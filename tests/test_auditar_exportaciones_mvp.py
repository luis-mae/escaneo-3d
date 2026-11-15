"""Auditoría de formatos: detecta archivos inexistentes y truncados."""
import struct
import tempfile
import unittest
from pathlib import Path

from tools.auditar_exportaciones_mvp import auditar_exportaciones


class AuditoriaExportacionesTests(unittest.TestCase):
    def test_sin_archivos_no_es_exito(self):
        with tempfile.TemporaryDirectory() as tmp:
            reporte = auditar_exportaciones(tmp)
            self.assertFalse(reporte["exportaciones_validas_basicas"])
            self.assertFalse(reporte["geometria_validada"])

    def test_detecta_stl_truncado_y_glb_invalido(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            (raiz / "modelo.obj").write_text(
                "v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n",
                encoding="utf-8",
            )
            (raiz / "modelo.stl").write_bytes(b"0" * 80 + struct.pack("<I", 2))
            (raiz / "modelo.glb").write_bytes(b"glTF" + struct.pack("<II", 2, 999) + b"12345678")
            reporte = auditar_exportaciones(raiz)
            self.assertTrue(reporte["archivos"]["obj"]["valido_basico"])
            self.assertFalse(reporte["archivos"]["stl"]["valido_basico"])
            self.assertFalse(reporte["archivos"]["glb"]["valido_basico"])
            self.assertFalse(reporte["exportaciones_validas_basicas"])


if __name__ == "__main__":
    unittest.main()
