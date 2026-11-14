# Avance 96 — Fusión directa de archivos PLY

Se agregó una CLI para cargar dos o más nubes PLY XYZ, registrarlas por ICP rígido contra una base, aplicar el control de cobertura y exportar PLY e informe JSON.

Ejemplo: `python -m tools.fusion_desde_ply a.ply b.ply --salida resultado --radio 0.1 --voxel 0.01`.

Incluye una prueba de integración de dos archivos PLY sintéticos. Requiere prealineación y escala comparable; no resuelve fotogrametría a partir de fotos. CI pendiente de verificación.
