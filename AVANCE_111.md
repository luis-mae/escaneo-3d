# Etapa 111 — Exportación automática COLMAP → PLY

El adaptador `tools/motor_colmap.py` ahora ejecuta `model_converter` para cada modelo disperso generado y crea `modelo_000.ply`, etc. El informe registra cada exportación y distingue reconstrucción exitosa de exportación incompleta. Si ningún PLY se produce, informa error y conserva el diagnóstico.

Se agregaron pruebas simuladas para el flujo completo y para una exportación fallida. **No se ejecutó COLMAP real ni la suite de CI**. Pendiente: instalación externa, ejecución con fotos reales y evaluación de calidad. La salida PLY sigue siendo dispersa y de escala arbitraria.
