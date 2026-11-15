"""Prueba de integración real PLY -> alpha-shape -> OBJ -> STL/GLB.

No requiere COLMAP ni fotos: comprueba la cadena geométrica y exportadora.
"""
import json
import struct
import tempfile
import unittest
from pathlib import Path

import numpy as np

from tools.colmap_a_malla import nube_colmap_a_malla
from tools.exportar_formatos_3d import exportar_formatos
from tools.reparar_malla import reparar_obj, leer_obj_triangulos


class FlujoGeometricoTests(unittest.TestCase):
    def test_nube_ply_a_obj_reparado_y_stl_glb(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nube = root / "nube.ply"
            # Tetraedro no coplanar con puntos interiores para simular nube COLMAP.
            vertices = np.array([[0., 0., 0.], [1., 0., 0.],
                                 [0., 1., 0.], [0., 0., 1.],
                                 [.15, .15, .15], [.25, .1, .1]])
            with nube.open("w", encoding="ascii") as f:
                f.write("ply\nformat ascii 1.0\nelement vertex 6\n")
                f.write("property float x\nproperty float y\nproperty float z\nend_header\n")
                for x, y, z in vertices:
                    f.write(f"{x} {y} {z}\n")
            original = root / "original.obj"
            informe = nube_colmap_a_malla(nube, original, alpha=5.0,
                                          max_puntos=100)
            self.assertTrue(original.exists())
            self.assertGreaterEqual(informe["caras"], 4)
            self.assertEqual(informe["metodo_superficie"], "alpha_shape")
            reparada = root / "reparada.obj"
            reparar_obj(original, reparada)
            v, caras = leer_obj_triangulos(reparada)
            self.assertGreaterEqual(len(v), 4)
            self.assertGreaterEqual(len(caras), 4)
            exportados = root / "exportados"
            reporte = exportar_formatos(reparada, exportados, ("obj", "stl", "glb"))
            self.assertEqual(len(reporte["archivos"]), 3)
            stl = (exportados / "modelo.stl").read_bytes()
            self.assertEqual(len(stl), 84 + 50 * struct.unpack_from("<I", stl, 80)[0])
            self.assertEqual(struct.unpack_from("<I", stl, 80)[0], len(caras))
            glb = (exportados / "modelo.glb").read_bytes()
            self.assertEqual(glb[:4], b"glTF")
            self.assertEqual(struct.unpack_from("<I", glb, 8)[0], len(glb))
            self.assertTrue((exportados / "informe_exportacion.json").is_file())


if __name__ == "__main__":
    unittest.main()
