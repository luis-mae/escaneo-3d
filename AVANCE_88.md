# Avance 88 — Protección numérica de fusión por vóxeles

La fusión controlada calcula índices de vóxel relativos al mínimo de la nube, en lugar de convertir directamente coordenadas absolutas a enteros. Se valida el rango de índices antes de la conversión, rechazando resoluciones demasiado pequeñas para representar la extensión de los datos sin pérdida de precisión.

Se incorporan pruebas con coordenadas de gran magnitud y vóxeles extremadamente pequeños.

**Pendiente:** verificar ejecución completa en CI y resultados con datos de escaneo reales. No hay aún garantía de precisión métrica.
