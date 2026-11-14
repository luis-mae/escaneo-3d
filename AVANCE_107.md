# Etapa 107 — Control de calidad reproducible

Se añadió `tools/calidad_sfm.py` con criterios de aceptación **solo para inspección experimental**: cantidad de puntos y cámaras, RMS de reproyección, profundidad positiva y fracción de observaciones bajo umbral. El pipeline `tools/fotos_a_nube_global.py` incluye el diagnóstico en `informe.json`, sin ocultar resultados cuando los umbrales no se cumplen.

Se agregaron pruebas sintéticas de aprobación, rechazo, ausencia de auditoría y valores no finitos. **Pendiente ejecutar las pruebas y validar fotografías reales.** Una aprobación no significa escala correcta, precisión física ni modelo imprimible.
