"""Pruebas del puente de importación sin iniciar COLMAP ni el servidor."""
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools.cola_persistente import ColaPersistente
from tools.importar_proyecto_worker import importar_proyecto


class ImportarProyectoWorkerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raiz = Path(self.tmp.name)
        self.origen = self.raiz / "api"
        self.base = self.raiz / "worker"
        self.identificador = "a" * 32
        self.proyecto = self.origen / self.identificador
        fotos = self.proyecto / "fotos"
        fotos.mkdir(parents=True)
        Image.new("RGB", (8, 8)).save(fotos / "foto.jpg")
        (self.proyecto / "estado.json").write_text(json.dumps({
            "id": self.identificador, "user_id": "usuario", "estado": "completado"
        }), encoding="utf-8")

    def test_importa_y_encola(self):
        self.assertEqual(importar_proyecto(self.origen, self.base, self.identificador, "usuario"), self.identificador)
        destino = self.base / "entradas" / self.identificador / "fotos" / "foto.jpg"
        self.assertTrue(destino.is_file())
        self.assertEqual(ColaPersistente(self.base / "cola.sqlite").consultar(self.identificador, "usuario")["estado"], "pendiente")

    def test_rechaza_propietario_distinto(self):
        with self.assertRaises(PermissionError):
            importar_proyecto(self.origen, self.base, self.identificador, "otro")
        self.assertFalse((self.base / "entradas" / self.identificador).exists())

    def test_rechaza_proyecto_activo(self):
        estado = self.proyecto / "estado.json"
        registro = json.loads(estado.read_text())
        registro["estado"] = "procesando"
        estado.write_text(json.dumps(registro))
        with self.assertRaises(ValueError):
            importar_proyecto(self.origen, self.base, self.identificador, "usuario")

    def test_rechaza_importacion_duplicada_sin_borrar_primera(self):
        importar_proyecto(self.origen, self.base, self.identificador, "usuario")
        destino = self.base / "entradas" / self.identificador / "fotos" / "foto.jpg"
        with self.assertRaises(FileExistsError):
            importar_proyecto(self.origen, self.base, self.identificador, "usuario")
        self.assertTrue(destino.is_file())

    def test_rechaza_symlink_en_fotos(self):
        fotos = self.proyecto / "fotos"
        (fotos / "extra.jpg").symlink_to(fotos / "foto.jpg")
        with self.assertRaises(ValueError):
            importar_proyecto(self.origen, self.base, self.identificador, "usuario")


if __name__ == "__main__":
    unittest.main()
