import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

from tools.entitlements import (
    configurar_cuenta, obtener_entitlements, reservar_trabajo, finalizar_trabajo,
    eliminar_cuenta
)


class TestEntitlements(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.patch = patch.dict(os.environ, {
            "ESCANEO3D_BILLING_DB": os.path.join(self.tmp.name, "usage.sqlite3")
        })
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def test_cuota_free_y_reserva(self):
        estado = configurar_cuenta("u1", "FREE")
        self.assertEqual(estado["disponibles"], 5)
        reserva = reservar_trabajo("u1", "job-1")
        self.assertEqual(reserva["cuota_restante"], 4)
        self.assertEqual(obtener_entitlements("u1")["disponibles"], 4)

    def test_reserva_idempotente(self):
        configurar_cuenta("u1", "FREE")
        reservar_trabajo("u1", "job-1")
        self.assertTrue(reservar_trabajo("u1", "job-1")["repetido"])
        self.assertEqual(obtener_entitlements("u1")["consumidos_o_reservados"], 1)

    def test_cuota_no_se_supera(self):
        configurar_cuenta("u1", "FREE")
        for i in range(5):
            reservar_trabajo("u1", f"job-{i}")
        with self.assertRaises(PermissionError):
            reservar_trabajo("u1", "job-extra")

    def test_fallo_libera_reserva(self):
        configurar_cuenta("u1", "FREE")
        reservar_trabajo("u1", "job-1")
        finalizar_trabajo("u1", "job-1", exito=False)
        self.assertEqual(obtener_entitlements("u1")["disponibles"], 5)

    def test_exito_consumo_no_se_libera(self):
        configurar_cuenta("u1", "FREE")
        reservar_trabajo("u1", "job-1")
        finalizar_trabajo("u1", "job-1", exito=True)
        self.assertEqual(obtener_entitlements("u1")["disponibles"], 4)

    def test_cuenta_inactiva_bloqueada(self):
        configurar_cuenta("u1", "PRO", active=False)
        with self.assertRaises(PermissionError):
            reservar_trabajo("u1", "job-1")

    def test_planes_con_cuotas_distintas(self):
        self.assertEqual(configurar_cuenta("plus", "PLUS")["cuota_mensual"], 25)
        self.assertEqual(configurar_cuenta("pro", "PRO")["cuota_mensual"], 50)

    def test_no_acepta_plan_desconocido(self):
        with self.assertRaises(ValueError):
            configurar_cuenta("u1", "ENTERPRISE")


    def test_reservas_concurrentes_respetan_limite(self):
        configurar_cuenta("u-concurrente", "FREE")
        barrera = Barrier(8)

        def intentar(i):
            barrera.wait()
            try:
                reservar_trabajo("u-concurrente", f"job-{i}")
                return True
            except PermissionError:
                return False

        with ThreadPoolExecutor(max_workers=8) as pool:
            resultados = list(pool.map(intentar, range(8)))
        self.assertEqual(sum(resultados), 5)
        self.assertEqual(obtener_entitlements("u-concurrente")["disponibles"], 0)

    def test_reserva_liberada_no_puede_reutilizarse(self):
        configurar_cuenta("u1", "FREE")
        reservar_trabajo("u1", "job-1")
        finalizar_trabajo("u1", "job-1", exito=False)
        with self.assertRaises(ValueError):
            reservar_trabajo("u1", "job-1")
        reservar_trabajo("u1", "job-2")
        self.assertEqual(obtener_entitlements("u1")["disponibles"], 4)

    def test_configuracion_rechaza_booleano_no_booleano(self):
        with self.assertRaises(ValueError):
            configurar_cuenta("u1", "FREE", active="false")

    def test_borrado_de_cuenta_elimina_derechos_de_uso(self):
        configurar_cuenta("u1", "FREE")
        reservar_trabajo("u1", "job-1")
        self.assertTrue(eliminar_cuenta("u1")["eliminada"])
        with self.assertRaises(KeyError):
            obtener_entitlements("u1")

if __name__ == "__main__":
    unittest.main()
