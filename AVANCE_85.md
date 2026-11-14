# Avance 85 — Control de calidad integrado en ICP

El resultado de `tools/registro_icp.py` ahora incorpora `auditoria_final` calculada sobre las nubes después de aplicar la transformación rígida estimada. Incluye cobertura bidireccional, errores RMSE y percentiles 95 de vecinos próximos, y el umbral utilizado. Las pruebas existentes de ICP ahora comprueban también la cobertura final en casos sintéticos.

**Estado:** código y pruebas guardados en GitHub; ejecución de GitHub Actions todavía no confirmada. La cobertura no certifica homología física ni exactitud métrica.
