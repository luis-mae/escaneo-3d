# Etapa 104 — Primer motor SfM incremental experimental

Se implementó `tools/sfm_incremental.py`, que recibe tracks 2D de `tools/tracks_desde_fotos.py`, calcula pose relativa inicial mediante matriz esencial, triangula puntos iniciales y registra vistas adicionales con PnP/RANSAC, incorporando nuevos puntos al sistema global. A diferencia de la etapa 103, las cámaras aceptadas comparten un sistema de coordenadas de reconstrucción, **pero la escala sigue siendo arbitraria**.

Uso:

```bash
python -m tools.tracks_desde_fotos foto1.jpg foto2.jpg foto3.jpg --salida tracks.json
python -m tools.sfm_incremental tracks.json --focal-px 1200 --ancho 1920 --alto 1080 --salida sfm_resultado
```

Se agregaron pruebas de validación y una escena sintética de dos cámaras. **Sin validación real ni confirmación de CI**. Limitaciones: focal estimada, secuencias difíciles, deriva, falta de bundle adjustment global y reconstrucción densa. No es una malla imprimible ni un escáner dimensional certificado.
