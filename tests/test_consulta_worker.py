import tempfile
import unittest
from pathlib import Path

from tools.cola_persistente import ColaPersistente
from tools.consulta_worker import consultar_trabajo


class ConsultaWorkerTest(unittest.TestCase):
    def test_sin_cola_no_crea_archivos(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "sin_datos"
            self.assertIsNone(consultar_trabajo(base, "a" * 32, "usuario"))
            self.assertFalse(base.exists())

    def test_solo_consulta_propietario(self):
        with tempfile.TemporaryDirectory() as tmp:
            cola = ColaPersistente(Path(tmp) / "cola.sqlite")
            cola.agregar("a" * 32, "usuario")
            self.assertEqual(consultar_trabajo(tmp, "a" * 32, "usuario")["estado"], "pendiente")
            self.assertIsNone(consultar_trabajo(tmp, "a" * 32, "otro"))

    def test_consulta_ruta_con_caracteres_reservados(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "cola #1 ? datos"
            cola = ColaPersistente(base / "cola.sqlite")
            cola.agregar("b" * 32, "usuario")
            self.assertEqual(
                consultar_trabajo(base, "b" * 32, "usuario")["estado"], "pendiente"
            )

    def test_rechaza_identificador_invalido(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                consultar_trabajo(tmp, "../etc/passwd", "usuario")


if __name__ == "__main__":
    unittest.main()
