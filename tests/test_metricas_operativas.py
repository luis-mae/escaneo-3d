import json
import tempfile
import unittest
from pathlib import Path

from tools.metricas_operativas import resumir


class MetricasOperativasTest(unittest.TestCase):
    def test_resumen_sin_identificadores(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            for i, estado in enumerate(("completado", "fallido", "cancelado", "procesando")):
                identificador = f"{i:032x}"
                carpeta = raiz / identificador
                carpeta.mkdir()
                (carpeta / "estado.json").write_text(json.dumps({
                    "id": identificador, "estado": estado,
                    "user_id": "privado", "duracion_total_segundos": 10,
                }), encoding="utf-8")
            salida = resumir(raiz)
            self.assertEqual(salida["proyectos"], 4)
            self.assertEqual(salida["finalizados"], 3)
            self.assertEqual(salida["tasa_exito_pct"], 33.33)
            self.assertNotIn("privado", json.dumps(salida))
            self.assertEqual(salida["duracion_media_segundos"], 10)

    def test_rechaza_estados_invalidos_y_no_divide_por_cero(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            identificador = "a" * 32
            carpeta = raiz / identificador
            carpeta.mkdir()
            (carpeta / "estado.json").write_text(
                json.dumps({"id": identificador, "estado": "inventado"}), encoding="utf-8")
            salida = resumir(raiz)
            self.assertEqual(salida["registros_invalidos"], 1)
            self.assertIsNone(salida["tasa_exito_pct"])

    def test_ignora_duraciones_no_finitas(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            identificador = "b" * 32
            carpeta = raiz / identificador
            carpeta.mkdir()
            (carpeta / "estado.json").write_text(
                json.dumps({"id": identificador, "estado": "completado",
                            "duracion_total_segundos": float("inf")}), encoding="utf-8")
            self.assertIsNone(resumir(raiz)["duracion_media_segundos"])


if __name__ == "__main__":
    unittest.main()
