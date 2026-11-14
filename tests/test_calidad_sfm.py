import unittest

from tools.calidad_sfm import evaluar_calidad_sfm


class TestCalidadSfm(unittest.TestCase):
    def informe(self):
        return {"puntos_3d": 30, "camaras": {"a": {}, "b": {}, "c": {}},
                "auditoria": {"rms_reproyeccion_px": 1.5,
                              "cobertura_profundidad": 0.95,
                              "fraccion_bajo_umbral": 0.85}}

    def test_aprueba_consistencia_interna(self):
        resultado = evaluar_calidad_sfm(self.informe())
        self.assertTrue(resultado["aprobado_para_inspeccion_experimental"])
        self.assertTrue(all(resultado["criterios"].values()))

    def test_rechaza_error_alto(self):
        informe = self.informe()
        informe["auditoria"]["rms_reproyeccion_px"] = 9.0
        resultado = evaluar_calidad_sfm(informe)
        self.assertFalse(resultado["aprobado_para_inspeccion_experimental"])
        self.assertFalse(resultado["criterios"]["rms_aceptable"])

    def test_rechaza_auditoria_ausente(self):
        informe = self.informe()
        del informe["auditoria"]
        self.assertFalse(evaluar_calidad_sfm(informe)["aprobado_para_inspeccion_experimental"])

    def test_rechaza_nan(self):
        informe = self.informe()
        informe["auditoria"]["rms_reproyeccion_px"] = float("nan")
        self.assertFalse(evaluar_calidad_sfm(informe)["aprobado_para_inspeccion_experimental"])

    def test_rechaza_umbrales_invalidos(self):
        with self.assertRaises(ValueError):
            evaluar_calidad_sfm(self.informe(), min_cobertura=1.2)

    def test_rechaza_pocas_camaras(self):
        informe = self.informe()
        informe["camaras"] = {"a": {}}
        self.assertFalse(evaluar_calidad_sfm(informe)["aprobado_para_inspeccion_experimental"])


if __name__ == "__main__":
    unittest.main()
