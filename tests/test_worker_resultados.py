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

    def test_no_publica_si_lease_es_reclamado_por_otro_worker(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            cola = ColaPersistente(base / "cola.db")
            identificador = "c" * 32
            cola.agregar(identificador, "usuario")

            def procesar(job, carpeta):
                (carpeta / "modelo.obj").write_text("malla")
                # Simula vencimiento y reclamo por otro worker mientras
                # el primero todavía ejecuta su callback.
                with cola._conexion() as db:
                    db.execute(
                        "UPDATE trabajos SET lease_hasta=0 WHERE id=?",
                        (job,),
                    )
                cola.reclamar_con_token("worker-2")

            resultado = ejecutar_con_resultados(cola, base, "worker-1", procesar)
            self.assertEqual(resultado.estado, "lease_perdido")
            self.assertFalse((base / "publicados" / identificador).exists())

    def test_fallo_limpia_temporales(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            cola = ColaPersistente(base / "cola.db")
            identificador = "f" * 32
            cola.agregar(identificador, "usuario")

            def procesar(job, carpeta):
                (carpeta / "parcial.ply").write_bytes(b"parcial")
                raise RuntimeError("fallo de reconstrucción")

            resultado = ejecutar_con_resultados(cola, base, "worker", procesar)
            self.assertEqual(resultado.estado, "fallido")
            self.assertEqual(list((base / "temporales" / identificador).glob("*")), [])
            self.assertFalse((base / "publicados" / identificador).exists())

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
