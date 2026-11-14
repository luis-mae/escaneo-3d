import tempfile
import unittest
from pathlib import Path

from tools.cola_persistente import ColaPersistente
from tools.worker_base import ejecutar_uno


class WorkerBaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cola = ColaPersistente(Path(self.tmp.name) / "cola.db")

    def tearDown(self):
        self.tmp.cleanup()

    def test_sin_trabajos(self):
        self.assertEqual(ejecutar_uno(self.cola, "w", lambda _: None).estado, "sin_trabajos")

    def test_exito(self):
        self.cola.agregar("a", "u")
        vistos = []
        resultado = ejecutar_uno(self.cola, "w", vistos.append)
        self.assertEqual(resultado.estado, "completado")
        self.assertEqual(vistos, ["a"])

    def test_fallo(self):
        self.cola.agregar("a", "u")
        def fallar(_):
            raise RuntimeError("fallo")
        resultado = ejecutar_uno(self.cola, "w", fallar)
        self.assertEqual(resultado.estado, "fallido")
        self.assertEqual(self.cola.consultar("a", "u")["estado"], "fallido")


if __name__ == "__main__":
    unittest.main()
