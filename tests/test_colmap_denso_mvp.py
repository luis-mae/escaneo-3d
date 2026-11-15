"""Pruebas del pipeline denso opcional sin ejecutar COLMAP real."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.colmap_denso_mvp import densificar_colmap


class DensoMvpTests(unittest.TestCase):
    def test_no_inicia_sin_gpu_cuda(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            fotos, sparse, salida = (raiz / x for x in ("fotos", "sparse", "denso"))
            fotos.mkdir()
            sparse.mkdir()
            for nombre in ("cameras.bin", "images.bin", "points3D.bin"):
                (sparse / nombre).write_bytes(b"contenido")
            with self.assertRaisesRegex(ValueError, "CUDA"):
                densificar_colmap(fotos, sparse, salida, usar_gpu=False)
            self.assertFalse(salida.exists())

    def test_fallo_paso_registra_informe_y_conserva_sparse(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            fotos, sparse, salida = (raiz / x for x in ("fotos", "sparse", "denso"))
            fotos.mkdir()
            sparse.mkdir()
            for nombre in ("cameras.bin", "images.bin", "points3D.bin"):
                (sparse / nombre).write_bytes(b"contenido")
            from subprocess import CompletedProcess
            with patch("tools.colmap_denso_mvp.shutil.which", return_value="colmap"), patch(
                "tools.colmap_denso_mvp.ejecutar_comando",
                return_value=CompletedProcess(["colmap"], 1, "", "fallo simulado"),
            ):
                with self.assertRaisesRegex(RuntimeError, "image_undistorter"):
                    densificar_colmap(fotos, sparse, salida, usar_gpu=True)
            self.assertTrue((salida / "ERROR_DENSO.txt").is_file())
            self.assertIn("incompleto", (salida / "informe_denso.json").read_text())
            self.assertTrue((sparse / "points3D.bin").is_file())


if __name__ == "__main__":
    unittest.main()
