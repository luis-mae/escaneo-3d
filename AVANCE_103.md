# Etapa 103 — Secuencias de fotografías por pares

Se agregó `tools/secuencia_fotografica.py`: procesa una lista ordenada de fotografías mediante pares consecutivos, exporta cada nube PLY e informe en directorios separados y escribe `resumen.json` con éxitos y fallos. Puede continuar cuando un par no permite reconstrucción.

Ejemplo: `python -m tools.secuencia_fotografica foto1.jpg foto2.jpg foto3.jpg --focal-px 1200 --salida resultados_secuencia`.

**Limitación fundamental:** las reconstrucciones por pares NO tienen una escala ni un sistema de coordenadas global común; por seguridad, no se fusionan automáticamente. Esto no es SfM multivista ni produce una malla global. Las pruebas de secuencia usan mocks y deben ejecutarse, además de validarse con imágenes reales.
