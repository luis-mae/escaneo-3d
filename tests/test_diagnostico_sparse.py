"""Pruebas del lector binario COLMAP, sin instalar COLMAP."""
import struct
import tempfile
import unittest
from pathlib import Path

from tools.diagnostico_sparse import diagnosticar


class DiagnosticoSparseTests(unittest.TestCase):
    def test_modelo_minimo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (root / "images.bin").open("wb") as f:
                f.write(struct.pack("<Q", 1))
                f.write(struct.pack("<I7dI", 1, 1, 0, 0, 0, 0, 0, 0, 1))
                f.write(b"foto01.jpg\\x00".replace(b"\\x00", bytes([0])))
                f.write(struct.pack("<Q", 1))
                f.write(struct.pack("<ddq", 12.0, 13.0, 10))
            with (root / "points3D.bin").open("wb") as f:
                f.write(struct.pack("<Q", 1))
                f.write(struct.pack("<Q3d3Bd", 10, 1.0, 2.0, 3.0, 255, 255, 255, 0.5))
                f.write(struct.pack("<QII", 1, 1, 0))
            result = diagnosticar(root)
            self.assertEqual(result["imagenes_registradas"], 1)
            self.assertEqual(result["nombres_imagenes"], ["foto01.jpg"])
            self.assertEqual(result["puntos_3d"], 1)
            self.assertEqual(result["puntos_con_track_de_2_o_mas"], 0)
            self.assertEqual(result["error_reproyeccion_maximo"], 0.5)
            self.assertEqual(result["longitud_track_media"], 1)
            self.assertEqual(result["error_reproyeccion_medio"], 0.5)

    def test_track_truncado(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "images.bin").write_bytes(struct.pack("<Q", 0))
            with (root / "points3D.bin").open("wb") as f:
                f.write(struct.pack("<Q", 1))
                f.write(struct.pack("<Q3d3Bd", 10, 1.0, 2.0, 3.0, 255, 255, 255, 0.5))
                f.write(struct.pack("<Q", 2))
                f.write(struct.pack("<II", 1, 0))
            with self.assertRaises(ValueError):
                diagnosticar(root)

    def test_observaciones_truncadas(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (root / "images.bin").open("wb") as f:
                f.write(struct.pack("<Q", 1))
                f.write(struct.pack("<I7dI", 1, 1, 0, 0, 0, 0, 0, 0, 1))
                f.write(b"foto.jpg" + bytes([0]))
                f.write(struct.pack("<Q", 2))
                f.write(struct.pack("<ddq", 1.0, 2.0, 1))
            (root / "points3D.bin").write_bytes(struct.pack("<Q", 0))
            with self.assertRaises(ValueError):
                diagnosticar(root)

    def test_archivo_truncado(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "images.bin").write_bytes(struct.pack("<Q", 1))
            (root / "points3D.bin").write_bytes(struct.pack("<Q", 0))
            with self.assertRaises(ValueError):
                diagnosticar(root)


if __name__ == "__main__":
    unittest.main()
