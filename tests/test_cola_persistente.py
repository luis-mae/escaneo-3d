import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.cola_persistente import ColaPersistente


class ColaPersistenteTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.cola = ColaPersistente(Path(self.temp.name) / "cola.db")

    def tearDown(self):
        self.temp.cleanup()

    def test_idempotencia_y_persistencia(self):
        self.assertTrue(self.cola.agregar("uno", "usuario"))
        self.assertFalse(self.cola.agregar("uno", "usuario"))
        otra = ColaPersistente(Path(self.temp.name) / "cola.db")
        self.assertEqual(otra.consultar("uno", "usuario")["estado"], "pendiente")
        self.assertIsNone(otra.consultar("uno", "otro"))

    def test_reclamo_renovacion_y_finalizacion(self):
        self.cola.agregar("uno", "usuario")
        self.assertEqual(self.cola.reclamar("worker"), "uno")
        self.assertIsNone(self.cola.reclamar("otro"))
        self.assertTrue(self.cola.renovar("uno", "worker"))
        self.assertFalse(self.cola.finalizar("uno", "otro", True))
        self.assertTrue(self.cola.finalizar("uno", "worker", True))
        self.assertEqual(self.cola.consultar("uno", "usuario")["estado"], "completado")

    def test_lease_expirado_y_reintento_limitado(self):
        self.cola.agregar("uno", "usuario")
        with patch("tools.cola_persistente.time.time", return_value=100):
            self.assertEqual(self.cola.reclamar("worker", segundos_lease=10, max_intentos=2), "uno")
        with patch("tools.cola_persistente.time.time", return_value=111):
            self.assertEqual(self.cola.reclamar("otro", max_intentos=2), "uno")
            self.assertFalse(self.cola.finalizar("uno", "worker", True))
        with patch("tools.cola_persistente.time.time", return_value=500):
            self.assertIsNone(self.cola.reclamar("tercero", max_intentos=2))

    def test_cancelacion_solo_propietario_y_pendiente(self):
        self.cola.agregar("uno", "usuario")
        self.assertFalse(self.cola.cancelar("uno", "otro"))
        self.assertTrue(self.cola.cancelar("uno", "usuario"))
        self.assertIsNone(self.cola.reclamar("worker"))


if __name__ == "__main__":
    unittest.main()
