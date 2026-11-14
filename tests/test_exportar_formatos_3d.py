import tempfile
import unittest
import json
import struct
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from tools.exportar_formatos_3d import exportar_formatos
from tools.verificar_stl import analizar


class TestExportarFormatos3D(unittest.TestCase):
    def test_exporta_tres_formatos(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            entrada = raiz / "malla.obj"
            entrada.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 0 1\n"
                               "f 1 3 2\nf 1 2 4\nf 1 4 3\nf 2 3 4\n")
            salida = raiz / "exportacion"
            informe = exportar_formatos(entrada, salida)
            self.assertEqual(len(informe["archivos"]), 3)
            self.assertEqual(analizar(salida / "modelo.stl")["triangulos"], 4)
            self.assertIn("element face 4", (salida / "modelo.ply").read_text())
            self.assertTrue((salida / "modelo.obj").exists())
            self.assertTrue((salida / "informe_exportacion.json").exists())


    def test_exporta_glb_2_y_valida_chunks(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            entrada = raiz / "malla.obj"
            entrada.write_text(chr(10).join(["v 0 0 0", "v 1 0 0", "v 0 1 0", "f 1 2 3", ""]))
            informe = exportar_formatos(entrada, raiz / "glb", ("glb",))
            archivo = raiz / "glb" / "modelo.glb"
            datos = archivo.read_bytes()
            magic, version, longitud = struct.unpack_from("<4sII", datos, 0)
            self.assertEqual(magic, b"glTF")
            self.assertEqual(version, 2)
            self.assertEqual(longitud, len(datos))
            longitud_json, tipo_json = struct.unpack_from("<I4s", datos, 12)
            self.assertEqual(tipo_json, b"JSON")
            documento = json.loads(datos[20:20 + longitud_json].decode().rstrip(" \\x00"))
            self.assertEqual(documento["asset"]["version"], "2.0")
            self.assertEqual(documento["meshes"][0]["primitives"][0]["mode"], 4)
            self.assertEqual(informe["archivos"][0]["archivo"], "modelo.glb")

    def test_exporta_3mf_core_con_relaciones_y_malla(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            entrada = raiz / "malla.obj"
            entrada.write_text("v 0 0 0\\nv 1 0 0\\nv 0 1 0\\nf 1 2 3\\n")
            informe = exportar_formatos(entrada, raiz / "3mf", ("3mf",))
            archivo = raiz / "3mf" / "modelo.3mf"
            self.assertEqual(informe["archivos"][0]["archivo"], "modelo.3mf")
            with zipfile.ZipFile(archivo) as paquete:
                self.assertIn("[Content_Types].xml", paquete.namelist())
                self.assertIn("_rels/.rels", paquete.namelist())
                self.assertIn("3D/3dmodel.model", paquete.namelist())
                xml = ET.fromstring(paquete.read("3D/3dmodel.model"))
                ns = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
                self.assertEqual(xml.attrib["unit"], "millimeter")
                self.assertEqual(len(xml.findall(".//m:vertex", ns)), 3)
                self.assertEqual(len(xml.findall(".//m:triangle", ns)), 1)

    def test_no_sobrescribe(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            entrada = raiz / "malla.obj"
            entrada.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
            salida = raiz / "salida"
            salida.mkdir()
            with self.assertRaises(FileExistsError):
                exportar_formatos(entrada, salida)

    def test_rechaza_formato_desconocido(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            entrada = raiz / "malla.obj"
            entrada.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
            with self.assertRaises(ValueError):
                exportar_formatos(entrada, raiz / "salida", ("exe",))

    def test_fallo_intermedio_limpia_exportacion_parcial(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            entrada = raiz / "malla.obj"
            entrada.write_text(
                "v 0 0 0\nv 1 0 0\nv 2 0 0\nf 1 2 3\n",
                encoding="utf-8",
            )
            salida = raiz / "exportacion"
            with self.assertRaisesRegex(ValueError, "degenerada"):
                exportar_formatos(entrada, salida)
            self.assertFalse(salida.exists())


if __name__ == "__main__":
    unittest.main()
