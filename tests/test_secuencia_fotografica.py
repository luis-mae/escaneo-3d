import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.secuencia_fotografica import procesar_secuencia


class TestSecuenciaFotografica(unittest.TestCase):
    def test_tres_fotos_dos_pares(self):
        with tempfile.TemporaryDirectory() as tmp:
            salida = Path(tmp) / "resultado"
            with patch("tools.secuencia_fotografica.reconstruir_y_exportar",
                       return_value={"aceptados": 25}) as reconstruir:
                resumen = procesar_secuencia(["a.jpg", "b.jpg", "c.jpg"], 1000, salida)
            self.assertEqual(reconstruir.call_count, 2)
            self.assertEqual(resumen["pares_con_nube"], 2)
            self.assertEqual(json.loads((salida / "resumen.json").read_text())["total_pares"], 2)
            self.assertEqual(resumen["estado"], "pares_independientes_sin_registro_global")

    def test_continua_si_un_par_falla(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("tools.secuencia_fotografica.reconstruir_y_exportar",
                       side_effect=[ValueError("pocos puntos"), {"aceptados": 15}]):
                resumen = procesar_secuencia(["a.jpg", "b.jpg", "c.jpg"], 1000, Path(tmp))
            self.assertEqual(resumen["pares_con_nube"], 1)
            self.assertEqual(resumen["pares"][0]["estado"], "fallido")
            self.assertEqual(resumen["pares"][1]["estado"], "experimental")

    def test_rechaza_salida_existente(self):
        with tempfile.TemporaryDirectory() as tmp:
            salida = Path(tmp)
            (salida / "resumen.json").write_text("{}")
            with self.assertRaises(FileExistsError):
                procesar_secuencia(["a.jpg", "b.jpg"], 1000, salida)

    def test_rechaza_fotos_repetidas(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "repetidas"):
                procesar_secuencia(["a.jpg", "a.jpg"], 1000, tmp)
