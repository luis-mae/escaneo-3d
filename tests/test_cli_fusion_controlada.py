"""Pruebas de integración de la interfaz de línea de comandos de fusión controlada."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from tools.verificar_exportacion import verificar_exportacion


class TestCLIControlada(unittest.TestCase):
    def setUp(self):
        self.nube = [[0, 0, 0], [1, 0, 0], [0, 2, 0],
                     [0, 0, 3], [1, 2, 3], [2, 1, 1]]

    def ejecutar(self, nubes, carpeta):
        entrada = carpeta / "entrada.json"
        entrada.write_text(json.dumps({"nubes": nubes}), encoding="utf-8")
        salida = carpeta / "resultado"
        comando = [sys.executable, "-m", "tools.fusion_con_control", str(entrada),
                   "--salida", str(salida), "--radio", "0.1", "--voxel", "0.01"]
        proceso = subprocess.run(comando, cwd=Path(__file__).resolve().parents[1],
                                 capture_output=True, text=True, timeout=30)
        return proceso, salida

    def test_exporta_ply_e_informe(self):
        with tempfile.TemporaryDirectory() as tmp:
            proceso, salida = self.ejecutar([self.nube, self.nube], Path(tmp))
            self.assertEqual(proceso.returncode, 0, proceso.stderr)
            informe = json.loads((salida / "informe_controlado.json").read_text(encoding="utf-8"))
            self.assertEqual(informe["puntos_salida"], 6)
            texto = (salida / "fusion_controlada.ply").read_text(encoding="ascii")
            self.assertIn("element vertex 6", texto)
            self.assertIn("end_header", texto)
            self.assertTrue((salida / "manifiesto_sha256.json").exists())
            verificacion = verificar_exportacion(salida)
            self.assertEqual(verificacion["estado"], "estructura_consistente")

    def test_no_sobrescribe_resultados_existentes(self):
        with tempfile.TemporaryDirectory() as tmp:
            carpeta = Path(tmp)
            primero, salida = self.ejecutar([self.nube, self.nube], carpeta)
            self.assertEqual(primero.returncode, 0, primero.stderr)
            anterior = (salida / "informe_controlado.json").read_bytes()
            segundo, _ = self.ejecutar([self.nube, self.nube], carpeta)
            self.assertNotEqual(segundo.returncode, 0)
            self.assertEqual((salida / "informe_controlado.json").read_bytes(), anterior)

    def test_no_exporta_si_datos_invalidos(self):
        with tempfile.TemporaryDirectory() as tmp:
            proceso, salida = self.ejecutar([self.nube, [[0, 0, 0]]], Path(tmp))
            self.assertNotEqual(proceso.returncode, 0)
            self.assertFalse((salida / "fusion_controlada.ply").exists())

    def test_rechazo_no_deja_archivos(self):
        with tempfile.TemporaryDirectory() as tmp:
            mala = [[x + 100 for x in p] for p in self.nube]
            proceso, salida = self.ejecutar([self.nube, mala], Path(tmp))
            self.assertNotEqual(proceso.returncode, 0)
            self.assertFalse((salida / "fusion_controlada.ply").exists())
            self.assertFalse((salida / "informe_controlado.json").exists())


if __name__ == "__main__":
    unittest.main()
