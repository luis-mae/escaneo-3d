# Avance 80 — Fusión robusta de nubes

Se añadió `tools/fusion_robusta.py`: aplica RANSAC Sim(3) a correspondencias 3D explícitas, transforma nubes al marco de la primera y permite agregación por voxel. Exporta PLY e informe JSON.

Uso: `python -m tools.fusion_robusta entrada.json --salida resultados --umbral 0.05 --voxel 0.01` desde el directorio `escaneo`. El JSON contiene `nubes` (listas de puntos XYZ) y `correspondencias` (una por nube posterior, cada una con `origen` y `destino` de puntos emparejados).

Límites: no obtiene correspondencias automáticamente de fotos, no certifica escala métrica ni calidad imprimible. Validar con datos reales.

Pruebas: 174 superadas en este entorno.
