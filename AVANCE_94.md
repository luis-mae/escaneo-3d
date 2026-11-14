# Avance 94 — Validación estricta del esquema PLY

El verificador de exportaciones ahora comprueba que el encabezado PLY declare exactamente tres propiedades `float`: `x`, `y` y `z`, en ese orden. Se agregaron pruebas para rechazar propiedades incompatibles y columnas adicionales.

Este control comprueba formato, no exactitud métrica. Pruebas de CI y escaneos reales aún pendientes de verificación.
