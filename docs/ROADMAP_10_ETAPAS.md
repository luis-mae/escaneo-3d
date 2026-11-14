# ESCANEO 3D — Hoja de ruta de producto en 10 etapas

Este documento reemplaza la numeración informal anterior para el cierre del producto. El avance se cierra con evidencia, no por cantidad de commits. Una prueba automatizada no sustituye una validación física.

## Etapa 1 — Validación integral del motor con objetos reales
**Objetivo:** demostrar el flujo completo fotografía → COLMAP/SfM → nube → malla → exportación, con objetos y dimensiones conocidas.
- Preflight automático de fotografías: resolución, exposición, detalle y duplicados aproximados.
- Ejecutar el motor con tres objetos de referencia: prismático, pieza con concavidad/agujero y objeto orgánico mate.
- Registrar logs, cámaras registradas, puntos, nube dispersa/densa, malla, tiempos y fallos.
- Comparar resultados en visor/CAD independiente; medir error solo tras calibrar escala.
- Definir fallos reproducibles y criterios de aprobación.
**Implementado en esta etapa:** preflight integrado al alta de proyectos, informe JSON descargable y resumen en interfaz. CI del commit `9878bf9`: 336 pruebas aprobadas, 1 warning y validación sintáctica/funcional de frontend aprobada.
**Pendiente imprescindible para cerrar la etapa:** sesión de fotografías reales y mediciones físicas; COLMAP real no se considera validado por mocks ni fixtures.
**Cierre:** tres casos reales documentados, incluyendo al menos un caso que falle y explicación de límites.

## Etapa 2 — Motor fotogramétrico robusto
- Revisar calibración de cámara, selección de pares, matching, registro incremental y optimización.
- Incorporar auditoría SfM en el pipeline: cámaras registradas, tracks, reproyección y cobertura.
- Reintentos controlados, timeouts, cancelación, logs claros y recuperación.
- Definir soporte CPU/GPU y versiones compatibles de COLMAP.
**Cierre:** reconstrucciones reproducibles con métricas y matriz de hardware.

## Etapa 3 — Malla útil y reparación geométrica
- Mejorar densificación, filtrado de outliers y reconstrucción de superficie.
- Reparación controlada de agujeros, normales, componentes y caras no-manifold.
- Clasificar mallas: vista previa, cerrada por aristas, lista para inspección; nunca afirmar imprimibilidad sin validación.
- Probar piezas finas, concavidades y oclusiones.
**Cierre:** mallas de objetos reales con informe de defectos y archivos reproducibles.

## Etapa 4 — Captura móvil guiada
- Aplicación Android/iOS con cámara, permisos y almacenamiento local.
- Guía de recorrido 360°, alturas, distancia, estabilidad y solapamiento.
- Detección de desenfoque/exposición y aviso en el momento de captura.
- Revisión de tomas, retomar/eliminar fotos, sesión recuperable y consentimiento.
**Cierre:** captura reproducible desde dispositivos reales y exportación segura de sesión.

## Etapa 5 — Visor, medición y gestión de modelos
- Visor de alta calidad, orientación, vistas y selección de modelos.
- Medición solo con escala validada; incertidumbre visible.
- Proyectos, historial, renombrar, duplicar, borrar y recuperar.
- Comparación de versiones y estado de calidad.
**Cierre:** usuario puede inspeccionar y gestionar un modelo real en teléfono y web.

## Etapa 6 — “Guardar o exportar a…” y formatos de destino
- Reemplazar acciones dispersas por una acción principal **Guardar o exportar a…**.
- Al abrirla, el usuario elige el destino/formato: STL (impresión 3D), OBJ (malla/intercambio), PLY (nube/malla), GLB (visualización/web), 3MF (fabricación) y opciones CAD.
- Mostrar qué contiene cada formato, compatibilidad, escala/unidades y limitaciones antes de guardar.
- STEP/IGES/DXF solo cuando la conversión correspondiente sea genuina y probada; no cambiar una extensión ni presentar una malla como CAD paramétrico.
- Paquetes ZIP y manifiesto de integridad.
**Cierre:** cada formato se abre correctamente en su aplicación destino con objetos de prueba.

## Etapa 7 — Backend remoto y procesamiento PRO
- API autenticada, almacenamiento privado, cola persistente y workers aislados.
- Subida cifrada, límites por archivo/proyecto, cancelación, reintentos y eliminación verificable.
- Procesamiento CPU/GPU medido, observabilidad, control de costos y cuotas.
- Separar datos de usuarios y trabajos; copias de seguridad y recuperación.
**Cierre:** flujo remoto seguro probado con cargas concurrentes y costos por trabajo.

## Etapa 8 — Cuentas, planes y pagos
- FREE/PLUS/PRO, cuotas y reglas de consumo transparentes.
- Login seguro y recuperación de cuenta; modo local sin cuenta cuando sea viable.
- Pagos/suscripciones según plataforma, facturación, cancelaciones y reembolsos.
- No fijar precios ni cuotas definitivas hasta conocer costos reales.
**Cierre:** pruebas de compra, renovación, cancelación, cuota y fallos de pago.

## Etapa 9 — Diseño visual y experiencia final
- Identidad visual ESCANEO 3D, sistema de diseño, iconografía y tipografía.
- Inicio con cuatro acciones: Nuevo escaneo, Mis modelos, Herramientas y **Guardar o exportar a…** cuando haya un modelo abierto.
- Flujos sencillos, onboarding, ayuda contextual, accesibilidad y estados vacíos/errores.
- Adaptación móvil/tablet/web, localización y modo oscuro/claro si aporta valor.
**Cierre:** prototipo visual aprobado y pruebas de usabilidad con usuarios.

## Etapa 10 — Seguridad, beta y publicación
- Auditoría de dependencias/licencias, privacidad, permisos y retención.
- Autenticación/autorización, aislamiento, protección de API, abuso y costos.
- Pruebas Android/iOS/PWA, rendimiento, batería, red, accesibilidad y recuperación.
- Beta cerrada, métricas de errores/uso con consentimiento, correcciones y checklist de tiendas.
- Publicación escalonada solo con autorización expresa.
**Cierre:** checklist aprobado, beta estable y publicación autorizada.

## Reglas de avance
- No declarar una etapa completa si depende de hardware, fotos, medidas o credenciales que no están disponibles.
- Se puede desarrollar en paralelo lo que no dependa de esos insumos, pero conservar las dependencias.
- No simular reconstrucción ni precisión física.
- Los artefactos se guardan en GitHub; las pruebas y su commit se verifican en Actions.
- El lanzamiento público requiere aprobación expresa.
