import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.cola_persistente import ColaPersistente
from tools.worker_colmap import procesar_colmap


class WorkerColmapTest(unittest.TestCase):
    def test_invoca_pipeline_y_publica(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            cola = ColaPersistente(base / "cola.sqlite")
            identificador = "a" * 32
            fotos = base / "entradas" / identificador / "fotos"
            fotos.mkdir(parents=True)
            (fotos / "foto.jpg").write_bytes(b"test")
            cola.agregar(identificador, "usuario")

            def simular(fotos_recibidas, salida, **kwargs):
                self.assertEqual(fotos_recibidas, fotos)
                self.assertIn('cancel_event', kwargs)
                self.assertFalse(kwargs['cancel_event'].is_set())
                (salida / "pipeline_colmap.json").write_text("{}")
                return {}

            with patch("tools.worker_colmap.pipeline_colmap", side_effect=simular):
                resultado = procesar_colmap(cola, base, "worker")
            self.assertEqual(resultado.estado, "completado")
            self.assertTrue(
                (base / "publicados" / identificador / "resultado" / "pipeline_colmap.json").exists())

    def test_directorio_fotos_symlink_no_se_procesa(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            cola = ColaPersistente(base / "cola.sqlite")
            identificador = "c" * 32
            (base / "entradas" / identificador).mkdir(parents=True)
            externa = base / "externa"
            externa.mkdir()
            (externa / "foto.jpg").write_bytes(b"test")
            (base / "entradas" / identificador / "fotos").symlink_to(
                externa, target_is_directory=True)
            cola.agregar(identificador, "usuario")
            with patch("tools.worker_colmap.pipeline_colmap") as motor:
                resultado = procesar_colmap(cola, base, "worker")
            self.assertEqual(resultado.estado, "fallido")
            motor.assert_not_called()

    def test_rechaza_archivos_no_admitidos(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            cola = ColaPersistente(base / "cola.sqlite")
            identificador = "d" * 32
            fotos = base / "entradas" / identificador / "fotos"
            fotos.mkdir(parents=True)
            (fotos / "foto.jpg").write_bytes(b"test")
            (fotos / "script.sh").write_text("echo no")
            cola.agregar(identificador, "usuario")
            with patch("tools.worker_colmap.pipeline_colmap") as motor:
                resultado = procesar_colmap(cola, base, "worker")
            self.assertEqual(resultado.estado, "fallido")
            motor.assert_not_called()

    def test_fotos_ausentes_marcan_fallo(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            cola = ColaPersistente(base / "cola.sqlite")
            cola.agregar("b" * 32, "usuario")
            with patch("tools.worker_colmap.pipeline_colmap") as motor:
                resultado = procesar_colmap(cola, base, "worker")
            self.assertEqual(resultado.estado, "fallido")
            motor.assert_not_called()


if __name__ == "__main__":
    unittest.main()
