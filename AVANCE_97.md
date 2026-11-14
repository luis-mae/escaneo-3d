# Avance 97 — Exportador único y verificado

Las interfaces de fusión desde JSON y desde archivos PLY comparten ahora `exportar_fusion`, que prepara PLY, informe y manifiesto SHA-256 en una carpeta temporal y verifica el contenido antes de publicar. Se actualizó la prueba de integración PLY para exigir manifiesto.

**Pendiente:** ejecutar CI y validar datos reales. La publicación de tres archivos sigue sin ser una transacción atómica conjunta.
