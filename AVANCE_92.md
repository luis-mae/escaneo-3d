# Avance 92 — Validación previa a la publicación de archivos

El exportador de fusión controlada ahora ejecuta `verificar_exportacion` sobre los archivos PLY y JSON temporales antes de moverlos a los nombres definitivos. Si la validación estructural falla, no se publican nuevos resultados. La prueba de integración verifica también la coherencia de la exportación generada.

**Pendientes:** ejecución efectiva de pruebas CI, reconstrucción completa desde fotografías reales y comprobación dimensional. La publicación de PLY y JSON no es una transacción atómica conjunta ante interrupciones.
