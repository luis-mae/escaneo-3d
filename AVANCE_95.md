# Avance 95 — Importación de nubes PLY XYZ

Nuevo lector de archivos PLY ASCII 1.0 para nubes XYZ, con validación de cabecera, cantidad máxima de puntos, coordenadas finitas, truncamientos y contenido adicional. Permite reutilizar nubes exportadas por el proyecto mediante Python.

Uso: `python -m tools.leer_ply nube.ply`. Se añadieron cuatro pruebas sintéticas, incluida ida y vuelta con `guardar_ply`.

Pendiente verificar CI y pruebas con archivos reales. No se admiten caras, colores ni PLY binarios.
