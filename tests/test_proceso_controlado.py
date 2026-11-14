import sys
import threading
import time
import unittest

from tools.proceso_controlado import ProcesoCancelado, ejecutar_comando


class TestProcesoControlado(unittest.TestCase):
    def test_ejecuta_y_captura_salida(self):
        resultado = ejecutar_comando(
            [sys.executable, "-c", "print('ok')"], 3
        )
        self.assertEqual(resultado.returncode, 0)
        self.assertEqual(resultado.stdout.strip(), "ok")

    def test_timeout_termina_proceso(self):
        with self.assertRaises(TimeoutError):
            ejecutar_comando(
                [sys.executable, "-c", "import time; time.sleep(5)"], 0.15
            )

    def test_cancelacion_termina_proceso(self):
        evento = threading.Event()
        hilo = threading.Thread(target=lambda: (time.sleep(0.15), evento.set()))
        hilo.start()
        inicio = time.monotonic()
        with self.assertRaises(ProcesoCancelado):
            ejecutar_comando(
                [sys.executable, "-c", "import time; time.sleep(5)"], 5,
                cancel_event=evento,
            )
        hilo.join()
        self.assertLess(time.monotonic() - inicio, 3)

    def test_cancelacion_previa_no_deja_proceso_activo(self):
        evento = threading.Event()
        evento.set()
        with self.assertRaises(ProcesoCancelado):
            ejecutar_comando(
                [sys.executable, "-c", "import time; time.sleep(5)"], 5,
                cancel_event=evento,
            )


if __name__ == "__main__":
    unittest.main()
