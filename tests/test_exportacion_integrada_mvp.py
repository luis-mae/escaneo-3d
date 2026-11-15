"""Prueba integrada real: OBJ -> STL/GLB -> auditoría de los tres formatos.

No requiere COLMAP ni fotos; confirma la cadena de exportación, no fidelidad 3D.
"""
import tempfile
import unittest
from pathlib import Path

from tools.exportar_formatos_3d import exportar_formatos
from tools.auditar_exportaciones_mvp import auditar_exportaciones


class ExportacionIntegradaTests(unittest.TestCase):
    def test_tetraedro_exporta_tres_formatos_validos(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            origen = raiz / "tetraedro.obj"
            origen.write_text(
                "v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 0 1\n"
                "f 1 3 2\nf 1 2 4\nf 1 4 3\nf 2 3 4\n",
                encoding="utf-8",
            )
            exportacion = exportar_formatos(
                origen, raiz / "exportados", ("obj", "stl", "glb")
            )
            auditoria = auditar_exportaciones(raiz / "exportados")
            self.assertEqual(exportacion["caras"], 4)
            self.assertEqual(exportacion["vertices"], 4)
            self.assertTrue(auditoria["exportaciones_validas_basicas"], auditoria)
            self.assertFalse(auditoria["geometria_validada"])
            self.assertFalse(auditoria["escala_validada"])


if __name__ == "__main__":
    unittest.main()
