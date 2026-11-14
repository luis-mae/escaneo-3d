# Etapa 102 — Trazabilidad de reconstrucción fotográfica

El flujo integrado registra SHA-256 del PLY y del OBJ opcional en el informe, para verificar que los resultados correspondan a los archivos exportados. Valida el número mínimo de puntos antes de procesar. El motor de dos vistas ahora informa resolución y focal utilizada cuando logra una reconstrucción experimental.

Pruebas ampliadas con comprobación del hash del PLY y rechazo de mínimo de puntos inválido. **Pendiente:** ejecución de CI, fotografías reales, escala y exactitud dimensional.
