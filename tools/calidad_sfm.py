"""Criterios de calidad configurables para SfM disperso experimental.

Una aprobación aquí solo significa que se cumplen umbrales internos; nunca
certifica precisión física, escala métrica ni aptitud de impresión.
"""
import math


def evaluar_calidad_sfm(informe, min_puntos=20, min_camaras=2,
                       max_rms_px=4.0, min_cobertura=0.85,
                       min_fraccion_bajo_umbral=0.7):
    if not isinstance(informe, dict):
        raise ValueError("Informe inválido")
    if type(min_puntos) is not int or min_puntos < 1:
        raise ValueError("min_puntos inválido")
    if type(min_camaras) is not int or min_camaras < 2:
        raise ValueError("min_camaras inválido")
    for nombre, valor in (("max_rms_px", max_rms_px),
                          ("min_cobertura", min_cobertura),
                          ("min_fraccion_bajo_umbral", min_fraccion_bajo_umbral)):
        if isinstance(valor, bool) or not isinstance(valor, (float, int)) or not math.isfinite(valor):
            raise ValueError(f"{nombre} inválido")
    if max_rms_px <= 0 or not 0 <= min_cobertura <= 1 or not 0 <= min_fraccion_bajo_umbral <= 1:
        raise ValueError("Umbrales fuera de rango")
    auditoria = informe.get("auditoria") or {}
    rms = auditoria.get("rms_reproyeccion_px")
    cobertura = auditoria.get("cobertura_profundidad")
    fraccion = auditoria.get("fraccion_bajo_umbral")
    puntos = informe.get("puntos_3d", 0)
    camaras = informe.get("camaras") or {}
    criterios = {
        "puntos_suficientes": type(puntos) is int and puntos >= min_puntos,
        "camaras_suficientes": isinstance(camaras, dict) and len(camaras) >= min_camaras,
        "rms_aceptable": isinstance(rms, (int, float)) and not isinstance(rms, bool)
                         and math.isfinite(rms) and 0 <= rms <= max_rms_px,
        "profundidad_positiva": isinstance(cobertura, (int, float)) and not isinstance(cobertura, bool)
                              and math.isfinite(cobertura) and cobertura >= min_cobertura and cobertura <= 1,
        "reproyecciones_bajo_umbral": isinstance(fraccion, (int, float)) and not isinstance(fraccion, bool)
                                   and math.isfinite(fraccion) and min_fraccion_bajo_umbral <= fraccion <= 1,
    }
    return {
        "aprobado_para_inspeccion_experimental": all(criterios.values()),
        "criterios": criterios,
        "umbrales": {"min_puntos": min_puntos, "min_camaras": min_camaras,
                     "max_rms_px": max_rms_px, "min_cobertura": min_cobertura,
                     "min_fraccion_bajo_umbral": min_fraccion_bajo_umbral},
        "advertencia": "Solo control interno de consistencia. No garantiza exactitud, escala ni aptitud para impresión."
    }
