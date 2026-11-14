"""Prueba de humo reproducible del flujo PLY -> registro -> fusión -> integridad."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

from tools.leer_ply import leer_ply_xyz
from tools.nube_dos_vistas import guardar_ply
from tools.verificar_exportacion import verificar_exportacion


class TestFlujoCompletoPLY(unittest.TestCase):
    def test_pipeline_reproducible(self):
        puntos = np.array([[0., 0., 0.], [1., 0., 0.], [0., 2., 0.],
                           [0., 0., 3.], [1., 2., 3.], [2., 1., 1.]])
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            primera, segunda = raiz / "primera.ply", raiz / "segunda.ply"
            salida = raiz / "salida"
            guardar_ply(puntos, primera)
            guardar_ply(puntos + np.array([0.02, 0., 0.]), segunda)
            np.testing.assert_allclose(leer_ply_xyz(primera), puntos)
            comando = [sys.executable, "-m", "tools.fusion_desde_ply",
                       str(primera), str(segunda), "--salida", str(salida),
                       "--radio", "0.1", "--voxel", "0.01"]
            resultado = subprocess.run(comando, capture_output=True, text=True,
                                      cwd=Path(__file__).resolve().parents[1], timeout=40)
            self.assertEqual(resultado.returncode, 0, resultado.stderr)
            verificacion = verificar_exportacion(salida)
            self.assertEqual(verificacion["vertices"], 6)
            informe = json.loads((salida / "informe_controlado.json").read_text())
            self.assertEqual(informe["puntos_entrada"], 12)
            self.assertEqual(informe["nubes"], 2)
            self.assertEqual(len(informe["registros"]), 1)
            self.assertTrue(informe["registros"][0]["registro"]["aprobado_para_fusion_experimental"])
            self.assertTrue((salida / "manifiesto_sha256.json").is_file())
            puntos_fusionados = leer_ply_xyz(salida / "fusion_controlada.ply")
            ordenar = lambda a: a[np.lexsort((a[:, 2], a[:, 1], a[:, 0]))]
            np.testing.assert_allclose(ordenar(puntos_fusionados), ordenar(puntos), atol=1e-6)

    def test_pipeline_rechaza_nubes_separadas(self):
        puntos = np.array([[0., 0., 0.], [1., 0., 0.], [0., 2., 0.],
                           [0., 0., 3.], [1., 2., 3.], [2., 1., 1.]])
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            a, b, salida = raiz / "a.ply", raiz / "b.ply", raiz / "salida"
            guardar_ply(puntos, a)
            guardar_ply(puntos + 100., b)
            resultado = subprocess.run(
                [sys.executable, "-m", "tools.fusion_desde_ply",
                 str(a), str(b), "--salida", str(salida), "--radio", "0.1"],
                capture_output=True, text=True, cwd=Path(__file__).resolve().parents[1],
                timeout=40)
            self.assertNotEqual(resultado.returncode, 0)
            self.assertFalse((salida / "fusion_controlada.ply").exists())
            self.assertFalse((salida / "manifiesto_sha256.json").exists())


if __name__ == "__main__":
    unittest.main()
