import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.cola_persistente import ColaPersistente


class ReclamoAtomicoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cola = ColaPersistente(Path(self.tmp.name) / "cola.sqlite")

    def tearDown(self):
        self.tmp.cleanup()

    def test_reclamo_devuelve_token_y_rechaza_anterior(self):
        self.cola.agregar("job", "owner")
        with patch("tools.cola_persistente.time.time", return_value=100):
            primero = self.cola.reclamar_con_token("worker", segundos_lease=10)
            self.assertEqual(primero[0], "job")
            self.assertTrue(self.cola.estado_reclamo(*("job", "worker", primero[1])))
        with patch("tools.cola_persistente.time.time", return_value=111):
            segundo = self.cola.reclamar_con_token("worker", segundos_lease=10)
            self.assertNotEqual(primero[1], segundo[1])
            self.assertFalse(self.cola.finalizar("job", "worker", True, token_lease=primero[1]))
            self.assertTrue(self.cola.finalizar("job", "worker", True, token_lease=segundo[1]))

    def test_reclamo_sin_trabajos(self):
        self.assertIsNone(self.cola.reclamar_con_token("worker"))

    def test_compatibilidad_reclamo_anterior(self):
        self.cola.agregar("job", "owner")
        self.assertEqual(self.cola.reclamar("worker"), "job")


if __name__ == "__main__":
    unittest.main()
