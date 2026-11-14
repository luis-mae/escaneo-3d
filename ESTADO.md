# Estado Escaneo3D

## Estado real al 14/11/2026
**Clasificación:** prototipo técnico avanzado; no validado ni publicable.

- Captura web: selección de fotografías y manifiesto local.
- API local: recepción de JPG/PNG, validación del contenido real, persistencia básica y seguimiento de estado.
- Motor: adaptador COLMAP integrado; el flujo web produce reconstrucción dispersa, no una malla densa validada.
- Malla/exportación: herramientas experimentales OBJ/PLY/STL; escala y aptitud de fabricación no certificadas.
- CI: 290 pruebas aprobadas en la última ejecución completa observada. La ejecución posterior a la limpieza del repositorio debe confirmarse.
- Pendiente: pruebas con fotografías reales, reconstrucción densa, robustez operativa, seguridad, dispositivos móviles y precisión métrica.

La numeración histórica de avances documenta tareas incorporadas; no equivale a porcentaje de producto terminado ni sustituye los criterios de aceptación.

## Historial de avances
Avance 07: conversión local STL/OBJ → STL, OBJ, PLY, sin servidores. No es CAD paramétrico. Pendiente motor de reconstrucción local.

Avance 08: exportación 3MF local (ZIP válido sin compresión, unidad mm explícita). Falta validar con slicers y dispositivos reales.

Avance 09: diagnóstico local STL/OBJ de topología, aristas abiertas, no-manifold, triángulos degenerados y caja dimensional. Sin reconstrucción fotogramétrica todavía.

## Avance 10
- Prototipo local experimental: segmentación de silueta, revolución geométrica y exportación STL sin servidor.
- Limitación explícita: NO es reconstrucción fotogramétrica multivista.
- Pendiente: motor real multivista y validación en dispositivos.

## Avance 11 — 2026-11-14
- Prototipo local de intersección de siluetas de cuatro vistas con exportación STL.
- Limitación explícita: no es fotogrametría multivista completa; requiere encuadre y fondo controlados.
- Pendiente: pruebas reales en dispositivos y reconstrucción fotogramétrica robusta.

## Avance 12 — segmentación mejorada
- Filtrado opcional de ruido por componente conexo mayor en las cuatro siluetas.
- Vista previa de las máscaras utilizadas para reconstrucción.
- Sigue siendo una aproximación experimental por siluetas, no fotogrametría calibrada.

## Avance 13 — refinamiento de siluetas
- Cierre morfológico opcional de huecos de 1 píxel antes de aislar el componente principal.
- Diagnóstico de porcentaje de silueta en cada vista.
- Recalcular límites de silueta al desactivar la limpieza de ruido.
- Sigue siendo un prototipo de visual hull, no fotogrametría ni reconstrucción CAD.

## Avance 14
- Control de coherencia de alturas de siluetas entre cuatro vistas.
- Informe JSON descargable con cobertura por imagen, resolución, triángulos y advertencias sobre escala y limitaciones.
- Motor multivista sigue siendo experimental; no equivale a fotogrametría ni a CAD paramétrico.

## Avance 27 — Verificación de archivos STL
- Herramienta `tools/verificar_stl.py`: lee STL ASCII/binario, informa dimensiones, triángulos degenerados, aristas abiertas y no-manifold.
- Prueba automatizada `tests/test_verificar_stl.py` ejecutada correctamente.
- Diagnóstico orientativo: una malla cerrada por aristas no implica precisión dimensional ni impresión garantizada.

## Avance 28 — limpieza conservadora STL
- Herramienta `tools/reparar_stl.py`: elimina triángulos degenerados y duplicados, exporta STL binario sin sobrescribir original.
- Pruebas automatizadas `tests/test_reparar_stl.py`.
- Advertencia: no cierra agujeros ni garantiza pieza imprimible.

## Avance 29 — 13/11/2026
- Nuevo `tools/cerrar_agujeros.py`: cierre experimental de contornos planos, convexos y pequeños; rechazo de contornos ambiguos.
- Pruebas unitarias agregadas; 6 pruebas correctas.
- No sustituye reparación industrial ni certifica imprimibilidad.

## Avance 30 — optimización STL conservadora
- Herramienta `tools/optimizar_stl.py`: soldadura de vértices cercanos mediante índice espacial, eliminación de caras colapsadas/duplicadas y reporte de resultados.
- Tolerancia configurable en unidades originales del archivo; no se presume que sean milímetros.
- No implementa reducción de polígonos ni garantiza imprimibilidad.
- Pruebas automáticas: 9 aprobadas en este paquete.
- Estado de integración GitHub: pendiente de repositorio disponible.

## Avance 32 — mediciones STL
- `tools/medir_stl.py`: dimensiones, área superficial y volumen condicionado a malla cerrada, orientada y sin degenerados.
- Unidad declarada obligatoria (mm, cm, m, pulgadas); STL no guarda unidades.
- Volumen no se informa cuando hay bordes abiertos, no-manifold o orientación inconsistente. No detecta autointersecciones.
- `tests/test_medir_stl.py`: cuatro pruebas nuevas; 16 pruebas totales correctas.
- Sigue pendiente fotogrametría real, pruebas móviles y repositorio GitHub.

### Avance 33 — auditoría topológica STL
- Nuevo `tools/auditar_malla.py`: componentes conectados, característica de Euler, vértices de borde ramificados, evaluación preliminar de aptitud para impresión.
- Nuevo `tests/test_auditar_malla.py`: casos de sólido cerrado, superficie abierta y dos componentes.
- 19 pruebas automatizadas superadas (`python -m unittest discover -s tests -q`).
- Advertencia: la auditoría no garantiza ausencia de autointersecciones, precisión dimensional ni imprimibilidad real.

### Avance 34 — reducción experimental de mallas
- `tools/reducir_malla.py`: agrupamiento espacial de vértices mediante celdas configurables; elimina triángulos colapsados y duplicados, conserva el archivo original y emite diagnóstico.
- `tests/test_reducir_malla.py`: cuatro pruebas nuevas; 23 pruebas automatizadas aprobadas.
- Limitación: la reducción puede modificar topología, detalle y precisión; no sustituye un decimador profesional ni garantiza impresión.
- GitHub sigue pendiente de creación/conexión del repositorio `escaneo`.

## Avance 42
Validación de alturas, márgenes de encuadre y referencia dimensional; métricas de calidad en JSON. Visual hull experimental, no fotogrametría métrica.

## Avance 43
- Validación de fotografías duplicadas por SHA-256, evitando contar imágenes idénticas como vistas diferentes.
- 40 pruebas automatizadas aprobadas.
- Pendiente reconstrucción fotogramétrica real y GitHub.

## Avance 44
- Nuevo `tools/inspeccionar_imagenes.py`: identifica dimensiones de PNG, JPEG y WebP VP8X mediante cabeceras, detecta resolución insuficiente y señala archivos no verificables sin afirmar que sean imágenes válidas.
- Nuevo `tests/test_inspeccionar_imagenes.py`: cuatro pruebas; 44 pruebas automatizadas superadas.
- Pendiente fotogrametría real y repositorio GitHub.

## Avance 46 — control fotográfico local
- Nuevo `tools/calidad_fotografias.py`: exposición, detalle aproximado, resolución y duplicados visuales aproximados, sin subir fotos ni modificar originales.
- `tests/test_calidad_fotografias.py` incluye pruebas de imágenes oscuras, duplicados y archivos dañados.
- Requiere Pillow. No equivale a una reconstrucción 3D ni garantiza exactitud dimensional.

## Avance 47 — preselección fotográfica
- `tools/seleccionar_fotografias.py`: filtra imágenes ilegibles, posibles duplicados y capturas con problemas evidentes de exposición, resolución o detalle; limita cantidad sin modificar originales.
- `tests/test_seleccionar_fotografias.py`: pruebas de rechazo y límites.
- Sigue pendiente motor fotogramétrico completo y repositorio GitHub.

## Avance 48 — preparación de sesión reproducible
- Nuevo `tools/preparar_sesion.py`: combina auditoría y preselección de imágenes, genera manifiesto JSON con hashes SHA-256 y tamaños para trazabilidad.
- Se evita escribir el manifiesto dentro del directorio de fotos para no contaminar la captura.
- 54 pruebas automatizadas pasan. No constituye reconstrucción fotogramétrica validada.

## Avance 49 — 2026-11-13
- Verificador de integridad SHA-256 de manifiestos fotográficos antes de enviar a un motor 3D.
- Rechaza rutas inseguras, nombres repetidos y detecta fotografías alteradas o faltantes.
- 57 pruebas automatizadas correctas.
- La reconstrucción fotogramétrica general todavía no está implementada ni validada.

## Avance 50 — integridad de sesión
- Verificador de manifiestos SHA-256 para detectar imágenes modificadas o faltantes antes de procesar.
- Bloqueo de rutas externas y nombres duplicados.
- 56 pruebas automatizadas superadas.
- La reconstrucción fotogramétrica general sigue pendiente de integración y validación real en dispositivos.

## Avance 51 — diagnóstico de correspondencias
Se agregó `tools/correspondencias.py`: ORB + filtrado de coincidencias + RANSAC para estimar solapamiento entre pares de fotos. OpenCV es una dependencia opcional. Esto **no** es todavía fotogrametría completa ni produce una malla 3D.

## Avance 52 — estimación experimental de cámaras
- `tools/estimar_camaras.py`: detección ORB, correspondencias, matriz esencial RANSAC y pose relativa con OpenCV.
- Validación de imágenes, resolución, focal e inliers; escala explícitamente desconocida.
- `tests/test_estimar_camaras.py`: tres casos de control.
- No equivale todavía a un motor SfM completo ni garantiza reconstrucción de piezas reales.

Avance 53: triangulación dispersa calibrada de dos vistas, con filtrado de profundidad y error de reproyección. No equivale a reconstrucción densa ni malla imprimible.

Avance 54: integración experimental de correspondencias ORB, estimación de pose, triangulación y exportación PLY dispersa en `tools/nube_dos_vistas.py`. Escala arbitraria; no es malla imprimible ni reconstrucción multivista completa.

## Avance 57 — secuencia de pares (experimental)
- `tools/nube_secuencia.py`: procesa fotos consecutivas y exporta PLY por par con informe JSON.
- No fusiona nubes: la escala y el marco de cada par son independientes. No es reconstrucción completa.
- `tests/test_nube_secuencia.py`: 3 pruebas superadas.

## Avance 60 — superficie preliminar desde nube unificada
- `tools/superficie_nube.py`: crea envolvente convexa triangular y exporta OBJ desde JSON de puntos 3D; corrige orientación de caras.
- `tests/test_superficie_nube.py`: cinco pruebas para geometría, orientación, errores y exportación.
- 79 pruebas totales superadas con unittest en el entorno de desarrollo.
- **Limitación importante:** la envolvente convexa elimina concavidades y huecos; NO representa una superficie fotogramétrica fiel ni una pieza apta para impresión. Requiere scipy/numpy y procesamiento Python; no integrado en móvil.
- Próximo paso: estimación de normales y reconstrucción de superficies no convexas con validación en fotografías reales.

## Avance 62 — diagnóstico de continuidad de superficies
- `tools/diagnosticar_superficie.py`: identifica aristas abiertas, bucles de contorno y aristas no-manifold; produce informe JSON.
- `tests/test_diagnosticar_superficie.py`: controles sintéticos para mallas cerradas, agujeros y geometría problemática.
- No cierra agujeros automáticamente: algunos son intencionales. No detecta autointersecciones ni garantiza impresión 3D.

## Avance 63 — reparación controlada de mallas
- `tools/reparacion_controlada.py`: limpieza y cierre opcional de agujeros pequeños, planos y convexos; informe comparativo antes/después; protección contra sobrescritura y guardado atómico.
- `tests/test_reparacion_controlada.py`: cinco pruebas nuevas.
- Verificación local: 89 pruebas `unittest` completadas correctamente (14/11/2026).
- Pendiente: validar con escaneos fotográficos reales, autointersecciones, espesores y medidas físicas. El porcentaje global previo es orientativo y no equivale a producto validado.

## Avance 64 — optimización de mallas
- Se agregó `tools/optimizar_malla.py`: simplificación experimental por agrupamiento espacial, descarte de caras degeneradas y duplicadas, auditoría e informe.
- No sobrescribe el STL original. La simplificación puede alterar topología y detalles: no implica aptitud certificada para impresión.
- Pruebas verificadas en este paquete: 95 (`python -m unittest discover -s tests -q`).

## Avance 66 — procesamiento de sesión fotográfica por pares
- `tools/reconstruir_sesion.py`: consume manifiesto de sesión, verifica SHA-256 de fotografías, ejecuta reconstrucción dispersa por pares consecutivos y guarda PLY independientes con informe de errores.
- `tests/test_reconstruir_sesion.py`: cinco pruebas nuevas sobre exportación, integridad, errores parciales, seguridad de ruta y focal.
- Verificación local de este paquete: 103 pruebas `unittest` superadas.
- **No hay reconstrucción multivista global ni escala común**. Cada PLY es independiente y no debe fusionarse sin estimación global de cámaras y ajuste de escala. Falta prueba con fotografías reales.

## Avance 67 — Marco común multivista
Se incorporó `tools/nube_marco_comun.py`: triangulación DLT multivista con matrices intrínsecas y extrínsecas globales suministradas, validación de profundidad positiva y reproyección, exportación PLY y reporte JSON. **No** calcula extrínsecas globales automáticamente a partir de fotos; la integración con el estimador de poses y el ajuste global sigue pendiente. Las unidades dependen de las traslaciones proporcionadas. Cinco pruebas sintéticas específicas agregadas.

## Avance 68 — poses secuenciales (experimental)
- `tools/poses_secuencia.py`: estima pose relativa entre fotos adyacentes con ORB/matriz esencial y encadena extrínsecas world->camera.
- Si un par no tiene suficientes correspondencias, la secuencia se detiene y registra diagnóstico.
- **Limitación importante:** cada traslación relativa se normaliza por separado; no hay escala global consistente, bundle adjustment ni cierre de bucle. No usar estas poses como calibración métrica validada.
- Pruebas nuevas: `tests/test_poses_secuencia.py` (5 casos sintéticos/de validación).

## Avance 70 — tracks multivista
- Incorporado `tools/tracks_multivista.py`: fusiona correspondencias de pares de imágenes en tracks de 2+ vistas y rechaza asociaciones contradictorias dentro de una imagen.
- 5 pruebas nuevas; suite completa: 126 pruebas superadas.
- Pendiente: conectar tracks con extracción real de características, poses de cámara y ajuste de haces; pruebas con fotografías reales.
- El porcentaje histórico de 98% no acredita que la app esté lista: falta validación integral y en celulares.

## Avance 71 — integración de tracks y cámaras
- Nuevo módulo `tools/integrar_tracks_camaras.py`: transforma tracks de correspondencias 2D en observaciones multivista, valida índices y cámaras, triangula en un marco común y exporta PLY + informe JSON.
- Cinco pruebas nuevas, sintéticas. Ejecución local: 131 pruebas aprobadas.
- Limitación crítica: exige poses globales calibradas; no se ha validado reconstrucción de fotos reales ni app móvil. Porcentajes históricos no son medida de completitud verificada.

## Avance 72 — Ajuste multivista experimental
- `tools/ajuste_multivista.py`: optimización robusta de puntos 3D y cámaras adicionales mediante mínimos cuadrados; ancla dos cámaras para eliminar libertad de escala.
- `tests/test_ajuste_multivista.py`: cuatro pruebas sintéticas nuevas.
- Verificación local: 135 pruebas aprobadas. Sin validación con fotos reales ni escala métrica.

## Avance 73 — integración de tracks y ajuste (experimental)
- Nuevo `tools/pipeline_ajuste_tracks.py`: triangula tracks 2D con cámaras calibradas conocidas, construye observaciones, ejecuta bundle adjustment y exporta PLY + JSON.
- Pruebas sintéticas adicionales: integración, rechazo de tracks inválidos y mínimos de puntos.
- Verificación local: 120 pruebas `unittest` correctas (13/11/2026). **No se probó con fotografías reales**.
- No resuelve calibración, poses automáticas, escala métrica ni ejecución móvil.

## Avance 74 — extracción de tracks desde fotografías
- Nuevo `tools/tracks_desde_fotos.py`: extrae características ORB de fotos reales, compara descriptores de pares consecutivos con coincidencia recíproca y filtra con matriz fundamental RANSAC.
- Exporta puntos 2D, tracks multivista y diagnósticos por par en JSON; las poses de cámaras aún deben estimarse aparte.
- Se añadieron 6 pruebas de entradas y correspondencias; suite completa ejecutada localmente: 126 pruebas correctas.
- Sin pruebas de precisión sobre un objeto real; no implica aplicación móvil terminada.

## Avance 75 — integración experimental de fotografías (13/11/2026)
- Nuevo `tools/reconstruir_par_fotos.py`: ORB + correspondencias + matriz esencial + pose relativa + triangulación filtrada por profundidad, error de reproyección y paralaje.
- Exportación de nube PLY e informe JSON. Escala arbitraria, no métrica.
- Pruebas sintéticas en `tests/test_reconstruir_par_fotos.py`.
- Pendiente: pipeline multivista completo, calibración real, escala métrica y pruebas con fotos reales/móvil.

## Avance 76 — pipeline multivista desde fotos (experimental)
- `tools/pipeline_fotos_multivista.py` une extracción de tracks, poses relativas encadenadas y triangulación en un flujo ejecutable; genera PLY y JSON.
- Uso: `python -m tools.pipeline_fotos_multivista foto1.jpg foto2.jpg foto3.jpg --focal-px 1200 --salida resultado/` desde la raíz del proyecto.
- Cuatro pruebas nuevas; suite local: 156 aprobadas, 8 advertencias.
- Limitación crítica: cada baseline entre fotos se normaliza por separado. **No se recupera escala global** y la geometría puede deformarse. No validado con imágenes reales; no apto para medidas ni impresión.

## Avance 79 — Registro robusto de escala
Se agregó `tools/registrar_escala_robusta.py`: estimación Sim(3) con RANSAC para pares 3D conocidos, filtrado de correspondencias atípicas, ajuste final e informe de inliers/outliers. Requiere correspondencias 3D ya establecidas; no corrige automáticamente cámaras ni valida fotos reales.
Ejemplo: `python tools/registrar_escala_robusta.py pares.json --salida registro.json --umbral 0.01`.
