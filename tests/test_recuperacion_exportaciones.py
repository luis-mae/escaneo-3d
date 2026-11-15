"""Regresión: recuperar descargas tras un reinicio durante el reemplazo."""
import json
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch


class RecuperacionExportaciones(unittest.TestCase):
    def test_restaurar_respaldo_y_formatos(self):
        from tools import servidor_web as servidor
        with tempfile.TemporaryDirectory() as temporal:
            raiz = Path(temporal)
            identificador = uuid.uuid4().hex
            proyecto = raiz / identificador
            resultado = proyecto / "resultado"
            respaldo = resultado / ("exportaciones_old_" + uuid.uuid4().hex)
            respaldo.mkdir(parents=True)
            (respaldo / "modelo.stl").write_bytes(b"STL anterior valido")
            (respaldo / "informe_exportacion.json").write_text(
                json.dumps({"archivos": [{"archivo": "modelo.stl"}]}),
                encoding="utf-8")
            registro = {
                "id": identificador, "nombre": "Recuperación",
                "estado": "completado", "malla": "completada",
                "exportaciones": "procesando",
                "exportaciones_formatos": ["glb"],
                "exportaciones_paquete": True,
            }
            (proyecto / "estado.json").write_text(
                json.dumps(registro), encoding="utf-8")
            with patch.object(servidor, "RAIZ", raiz):
                try:
                    servidor._recuperar_estados()
                    recuperado = servidor.ESTADOS[identificador]
                    self.assertEqual(recuperado["exportaciones"], "completadas")
                    self.assertEqual(recuperado["exportaciones_formatos"], ["stl"])
                    self.assertFalse(recuperado["exportaciones_paquete"])
                    self.assertTrue(
                        (resultado / "exportaciones" / "modelo.stl").is_file())
                    self.assertFalse(respaldo.exists())
                finally:
                    servidor.ESTADOS.pop(identificador, None)

    def test_no_anunciar_formato_perdido(self):
        from tools import servidor_web as servidor
        with tempfile.TemporaryDirectory() as temporal:
            raiz = Path(temporal)
            identificador = uuid.uuid4().hex
            proyecto = raiz / identificador
            exportados = proyecto / "resultado" / "exportaciones"
            exportados.mkdir(parents=True)
            (exportados / "informe_exportacion.json").write_text(
                "{}", encoding="utf-8")
            (proyecto / "estado.json").write_text(json.dumps({
                "id": identificador, "nombre": "Incompleto",
                "estado": "completado", "malla": "error",
                "exportaciones": "completadas",
                "exportaciones_formatos": ["glb"],
                "exportaciones_paquete": False,
            }), encoding="utf-8")
            with patch.object(servidor, "RAIZ", raiz):
                try:
                    servidor._recuperar_estados()
                    self.assertEqual(
                        servidor.ESTADOS[identificador]["exportaciones"],
                        "interrumpido")
                finally:
                    servidor.ESTADOS.pop(identificador, None)


if __name__ == "__main__":
    unittest.main()
