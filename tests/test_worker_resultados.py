import tempfile
import unittest
from pathlib import Path

from tools.cola_persistente import ColaPersistente
from tools.worker_resultados import ejecutar_con_resultados


class WorkerResultadosTest(unittest.TestCase):
    def test_publica_resultado_de_callback(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            cola = ColaPersistente(base / "cola.db")
            identificador = "a" * 32
            cola.agregar(identificador, "usuario")

            def procesar(job, carpeta):
                self.assertEqual(job, identificador)
                (carpeta / "modelo.obj").write_text("v 0 0 0\n")

            resultado = ejecutar_con_resultados(cola, base, "worker", procesar)
            self.assertEqual(resultado.estado, "completado")
            self.assertEqual(
                (base / "publicados" / identificador / "resultado" / "modelo.obj").read_text(),
                "v 0 0 0\n",
            )

    def test_error_no_publica(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            cola = ColaPersistente(base / "cola.db")
            identificador = "b" * 32
            cola.agregar(identificador, "usuario")

            def procesar(job, carpeta):
                raise RuntimeError("simulado")

            resultado = ejecutar_con_resultados(cola, base, "worker", procesar)
            self.assertEqual(resultado.estado, "fallido")
            self.assertFalse((base / "publicados" / identificador).exists())


if __name__ == "__main__":
    unittest.main()
