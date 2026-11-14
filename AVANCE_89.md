# Avance 89 — Pruebas de integración del exportador

Se incorporaron dos pruebas de extremo a extremo del **subproceso de fusión de nubes ya reconstruidas**, mediante el comando real `python -m tools.fusion_con_control`. Verifican que una fusión válida produzca archivos PLY e informe JSON, y que una nube rechazada no deje exportaciones.

Estas pruebas no abarcan la captura de fotografías ni la reconstrucción fotogramétrica completa. La ejecución en GitHub Actions sigue pendiente de verificación.
