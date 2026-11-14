# Etapa 109 — Bloqueo opcional de exportaciones de baja calidad

`tools/fotos_a_nube_global.py` incorpora `--exigir-calidad`: cuando el control de consistencia geométrica falla, detiene la exportación y comunica los criterios incumplidos. Sin el indicador, conserva el comportamiento anterior y registra los diagnósticos en el informe.

Ejemplo: `python -m tools.fotos_a_nube_global foto1.jpg foto2.jpg foto3.jpg --focal-px 1200 --salida salida --exigir-calidad`.

Se agregó una prueba que simula alto error de reproyección y verifica que no se publique una nube defectuosa. **Pendiente ejecutar la suite y probar fotografías reales**. La aprobación de calidad interna no equivale a exactitud métrica.
