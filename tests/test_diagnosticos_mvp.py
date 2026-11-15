"""Pruebas del diagnóstico de fallo y recuperación de sesiones con muchos archivos."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.procesar_nube_mvp import procesar_nube_mvp
from tools.verificar_sesion_mvp import verificar_sesion


def escribir_ply(ruta):
    ruta.write_text(
        "ply\nformat ascii 1.0\nelement vertex 4\n"
        "property float x\nproperty float y\nproperty float z\n"
        "end_header\n0 0 0\n1 0 0\n0 1 0\n0 0 1\n",
        encoding="ascii",
    )


class DiagnosticosMvpTests(unittest.TestCase):
    def test_reconoce_nube_despues_de_200_archivos_invalidos(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            for i in range(205):
                (raiz / f"a{i:03d}.ply").write_text("invalido", encoding="ascii")
            nube = raiz / "modelo_000.ply"
            escribir_ply(nube)
            reporte = verificar_sesion(raiz)
            self.assertEqual(reporte["reutilizar_nube"], str(nube))

    def test_conserva_causa_de_error_de_mallado(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            nube = raiz / "entrada.ply"
            escribir_ply(nube)
            salida = raiz / "salida"
            with patch("tools.procesar_nube_mvp.nube_colmap_a_malla",
                       side_effect=RuntimeError("fallo de triangulacion")):
                with self.assertRaisesRegex(RuntimeError, "triangulacion"):
                    procesar_nube_mvp(nube, salida, alpha=5)
            error = (salida / "ERROR.txt").read_text(encoding="utf-8")
            self.assertIn("fallo de triangulacion", error)
            self.assertIn("RuntimeError", error)


if __name__ == "__main__":
    unittest.main()
