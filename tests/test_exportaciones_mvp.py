"""Prueba integral de conversión OBJ a los cinco formatos de salida del MVP."""
import json
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.exportar_formatos_3d import exportar_formatos


class ExportacionesMvp(unittest.TestCase):
    def test_cinco_formatos_con_geometria_real(self):
        with tempfile.TemporaryDirectory() as temporal:
            raiz = Path(temporal)
            origen = raiz / "tetraedro.obj"
            origen.write_text(
                "v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 0 1\n"
                "f 1 3 2\nf 1 2 4\nf 1 4 3\nf 2 3 4\n",
                encoding="utf-8",
            )
            destino = raiz / "exportados"
            informe = exportar_formatos(
                origen, destino, formatos=("obj", "ply", "stl", "glb", "3mf")
            )
            self.assertEqual(informe["vertices"], 4)
            self.assertEqual(informe["caras"], 4)
            self.assertEqual(len(informe["archivos"]), 5)
            for extension in ("obj", "ply", "stl", "glb", "3mf"):
                archivo = destino / ("modelo." + extension)
                self.assertTrue(archivo.is_file(), extension)
                self.assertGreater(archivo.stat().st_size, 20, extension)
            self.assertTrue((destino / "modelo.ply").read_bytes().startswith(b"ply\n"))
            self.assertTrue((destino / "modelo.glb").read_bytes().startswith(b"glTF"))
            stl = (destino / "modelo.stl").read_bytes()
            self.assertEqual(struct.unpack_from("<I", stl, 80)[0], 4)
            self.assertEqual(len(stl), 84 + 50 * 4)
            with zipfile.ZipFile(destino / "modelo.3mf") as paquete:
                self.assertIn("3D/3dmodel.model", paquete.namelist())
            manifiesto = json.loads(
                (destino / "informe_exportacion.json").read_text(encoding="utf-8")
            )
            self.assertEqual(len(manifiesto["archivos"]), 5)


if __name__ == "__main__":
    unittest.main()
