import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
from tools.nube_dos_vistas import guardar_ply
from tools.verificar_exportacion import verificar_exportacion


class TestFusionDesdePLY(unittest.TestCase):
    def test_dos_ply_identicos(self):
        puntos = np.array([[0., 0, 0], [1, 0, 0], [0, 2, 0],
                           [0, 0, 3], [1, 2, 3], [2, 1, 1]])
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            a, b, salida = raiz / "a.ply", raiz / "b.ply", raiz / "salida"
            guardar_ply(puntos, a)
            guardar_ply(puntos, b)
            proc = subprocess.run([sys.executable, "-m", "tools.fusion_desde_ply",
                                   str(a), str(b), "--salida", str(salida),
                                   "--radio", "0.1", "--voxel", "0.01"],
                                  cwd=Path(__file__).resolve().parents[1],
                                  capture_output=True, text=True, timeout=30)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(verificar_exportacion(salida)["vertices"], 6)
            self.assertTrue((salida / "manifiesto_sha256.json").exists())


if __name__ == "__main__":
    unittest.main()
