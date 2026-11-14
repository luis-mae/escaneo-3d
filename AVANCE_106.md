# Etapa 106 — Auditoría de reconstrucción multivista

Se añadió `tools/auditar_sfm.py`, integrado en `tools/sfm_incremental.py`. Cada reconstrucción informa cobertura de profundidad positiva, RMS y percentil 95 de error de reproyección en píxeles, fracción bajo umbral y estadísticas por cámara. Se conserva la relación entre puntos 3D e índices de tracks originales para auditoría posterior.

Se incorporaron pruebas sintéticas de proyección exacta y validaciones de entradas. La auditoría no garantiza precisión métrica ni elimina el riesgo de geometría incorrecta. Pendientes: ejecutar CI y validar fotografías reales.
