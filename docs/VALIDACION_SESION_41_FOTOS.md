# Prueba de aceptación MVP con la sesión de 41 fotos (15/11/2026)

## Evidencia externa previa
La sesión manual del usuario produjo una nube COLMAP de aproximadamente 7.617 puntos y una malla Poisson en MeshLab de 16.515 vértices y 33.876 caras. Se exportó OBJ. **Estos números no prueban el funcionamiento del backend de la app**, ni certifican la forma del objeto: la geometría se observó deformada. El STL no está confirmado.

## Reproducir en la app local
1. Conservar los originales de las 41 fotografías. No reemplazarlos por imágenes sin fondo antes de la primera prueba: quitar el fondo puede reducir los puntos de coincidencia de COLMAP. Comparar ambas variantes en proyectos separados.
2. Ejecutar el servidor local según README, abrir la PWA y crear proyecto con las fotografías.
3. Procesar con COLMAP CPU y guardar `informe_colmap.json`. Registrar imágenes registradas, puntos, error de reproyección y duración. Si el equipo admite la fase densa, ejecutar otra prueba separada.
4. Generar la malla desde la interfaz: primero sin filtrado; después en un proyecto comparable, con `filtrar_ruido=true`. El filtrado es experimental y puede quitar detalles finos.
5. Comparar la geometría en el visor, descargar OBJ y STL mediante «Guardar o exportar a…» y abrir ambos en un visor independiente.
6. Documentar si la forma es reconocible, si el objeto está separado del fondo, si hay agujeros o superficies falsas, y qué porcentaje de fotografías se registró.
7. Medir dimensiones únicamente con escala física calibrada. No interpretar las coordenadas arbitrarias de COLMAP como milímetros.

## Condición de cierre
No declarar MVP funcional hasta ejecutar y documentar al menos una reconstrucción real completa **desde la interfaz**, con exportación OBJ y STL verificadas. La existencia de endpoints, tests o archivos exportados manualmente no basta.
