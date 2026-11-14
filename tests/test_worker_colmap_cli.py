import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from contextlib import redirect_stdout

from tools.worker_base import ResultadoWorker
from tools.worker_colmap_cli import main


class WorkerColmapCliTest(unittest.TestCase):
    def test_invoca_worker_y_emite_estado(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("tools.worker_colmap_cli.shutil.which", return_value="/usr/bin/colmap"):
                with patch("tools.worker_colmap_cli.procesar_colmap", return_value=ResultadoWorker(None, "sin_trabajos")) as ejecutar:
                    salida = io.StringIO()
                    with redirect_stdout(salida):
                        codigo = main(["--base", tmp, "--worker", "nodo-1"])
            self.assertEqual(codigo, 0)
            self.assertIn('"sin_trabajos"', salida.getvalue())
            ejecutar.assert_called_once()

    def test_no_permite_lease_corto(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                main(["--base", tmp, "--worker", "nodo-1", "--lease", "0"])


if __name__ == "__main__":
    unittest.main()
