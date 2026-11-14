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
- [x] Adaptador COLMAP con extracción de características, matching exhaustivo, mapper incremental y exportación PLY.
- [x] Reconstrucción densa opcional con PatchMatch Stereo y fusión.
- [x] Timeouts por comando y presupuesto global de tiempo compartido entre fases; captura de stdout/stderr.
- [x] Duración individual de fases y duración total del pipeline en segundos.
- [ ] Reintentos controlados, cancelación desde interfaz y recuperación de trabajos interrumpidos.
- [ ] Matriz de compatibilidad CPU/GPU, versiones y pruebas con datasets de referencia.
- [ ] Validación de calibración, reproyección, cobertura y robustez con capturas reales.
**Cierre:** reconstrucciones reproducibles con métricas y matriz de hardware.

## Etapa 3 — Malla útil y reparación geométrica
- Mejorar densificación, filtrado de outliers y reconstrucción de superficie.
- Reparación controlada de agujeros, normales, componentes y caras no-manifold.
- Clasificar mallas: vista previa, cerrada por aristas, lista para inspección; nunca afirmar imprimibilidad sin validación.
- Probar piezas finas, concavidades y oclusiones.
**Cierre:** mallas de objetos reales con informe de defectos y archivos reproducibles.

## Etapa 4 — Captura móvil guiada
- [x] PWA con manifiesto, icono, instalación y caché de interfaz; la API y los datos de proyectos no se cachean.
- [x] Captura desde cámara trasera del móvil y acumulación de fotografías en la sesión.
- [x] Guía de recorrido: 12 vistas horizontales + 8 elevadas, con orientación por toma.
- [x] Revisión individual y eliminación de fotografías antes de enviar.
- [x] Preflight posterior a la carga con resolución, exposición, detalle y duplicados aproximados.
- [ ] Aplicación Android/iOS nativa o contenedor móvil con cámara, permisos y almacenamiento local.
- [x] Guía de recorrido con indicaciones de ángulo, altura, distancia y solapamiento.
- [ ] Detección de desenfoque/exposición en el momento de captura.
- [ ] Guardado y recuperación de sesión local tras cerrar o perder la PWA.
**Cierre:** captura reproducible desde dispositivos reales y exportación segura de sesión. La PWA actual es una base, no equivale a una app nativa terminada.

## Etapa 5 — Visor, medición y gestión de modelos
- [x] Visor 3D web experimental con rotación, zoom y restablecimiento.
- [x] Biblioteca de proyectos del servidor local con selección y reapertura.
- [x] Eliminación de proyectos y sus archivos, con bloqueo durante trabajos activos.
- [x] Renombrado de proyectos sin alterar archivos de reconstrucción.
- [x] Calibración de escala global desde el visor con dos referencias físicas, control de discrepancia y exportación OBJ en mm.
- [ ] Herramienta de medición de distancias/volúmenes con incertidumbre visible y validación física independiente.
- [x] Duplicar proyectos y sus resultados en la biblioteca local.
- [ ] Comparar versiones y sincronización multi-dispositivo.
- [ ] Visor móvil optimizado para mallas grandes y dispositivos de gama baja.
**Cierre:** usuario puede inspeccionar y gestionar un modelo real en teléfono y web.

## Etapa 6 — “Guardar o exportar a…” y formatos de destino
- [x] Acción principal **Guardar o exportar a…**.
- [x] Selector de formatos con propósito explicado: STL, OBJ, PLY y GLB.
- [x] Exportador GLB 2.0 binario autocontenido con posiciones e índices triangulares.
- [x] Exportación separada de la nube PLY original de COLMAP, sin confundirla con la malla PLY.
- [x] Backend recibe solo los formatos elegidos y prepara las descargas correspondientes.
- [x] Exportación 3MF Core como paquete OPC con geometría triangular y metadatos de unidad asumida.
- [x] Advertencias sobre escala no verificada y diferencia entre malla y CAD paramétrico.
- [ ] Incorporar formatos CAD paramétricos/técnicos (STEP, IGES, DXF) mediante conversores reales, con licencia y pruebas de interoperabilidad.
- [ ] Validar GLB y 3MF en slicers/visores externos con objetos físicos de referencia.
- [ ] Agregar materiales/texturas si la captura los soporta.
- [x] Paquete ZIP opcional de los formatos elegidos, con informe de integridad y SHA-256 por archivo.
**Cierre:** cada formato se abre correctamente en su aplicación destino con objetos de prueba.

## Etapa 7 — Backend remoto y procesamiento PRO
- [x] Empaquetado reproducible del servidor y COLMAP CPU en Docker.
- [x] Persistencia de proyectos locales mediante volumen Docker.
- [x] Límites locales de carga y concurrencia; procesamiento pesado serializado.
- [x] Informes de ejecución con tiempos por fase y logs resumidos de COLMAP.
- [x] Base de autenticación JWT HS256 opcional, aislamiento por propietario, consulta de entitlements y control de cuota por trabajo.
- [x] Persistencia de la cuota, consumo al completar, liberación al fallar/reiniciar y borrado de cuenta/proyectos.
- [ ] Integrar proveedor de identidad real y gestión de sesión segura desde la PWA.
- [ ] API pública tras gateway HTTPS, almacenamiento privado y cola persistente distribuida.
- [ ] Workers aislados con cancelación, reintentos, límites CPU/GPU y borrado verificable.
- [ ] Instrumentación de costos, cuotas, backups y recuperación multiusuario.
**Cierre:** flujo remoto seguro probado con cargas concurrentes y costos por trabajo.

## Etapa 8 — Cuentas, planes y pagos
- [x] Motor transaccional SQLite para entitlements FREE/PLUS/PRO, cuotas mensuales, reservas idempotentes y liberación/consumo de trabajos.
- [x] Vinculación del subject JWT verificado a la cuenta y a la cuota de reconstrucción; provisionamiento administrativo solo local.
- [x] Endpoint autenticado de eliminación de cuenta y borrado de proyectos/archivos; bloquea eliminación mientras haya trabajos activos.
- [ ] Checkout y suscripciones reales; pagos, webhooks, facturación y cancelaciones.
- [ ] Login seguro y recuperación de cuenta; modo local sin cuenta cuando sea viable.
- [ ] Integrar proveedor de pagos, webhooks firmados, facturación, cancelaciones y reembolsos.
- [ ] Definir cuotas y precios finales tras medir costos reales; los valores actuales son preliminares.
**Cierre:** pruebas de compra, renovación, cancelación, cuota y fallos de pago.

## Etapa 9 — Diseño visual y experiencia final
- [x] Identidad visual inicial, paleta, tipografía, icono y estilos responsive.
- [x] Navegación entre Nuevo escaneo y Mis modelos.
- [x] Flujo visual en cuatro pasos: fotografiar, reconstruir, inspeccionar y exportar.
- [x] Ayuda de captura, estados accesibles y progreso indeterminado sin porcentajes inventados.
- [x] Biblioteca de proyectos con acciones de abrir, renombrar, duplicar y eliminar.
- [x] Guía de uso para captura, reconstrucción, inspección y formatos de salida.
- [ ] Onboarding interactivo, pruebas de usabilidad y accesibilidad completa.
- [ ] Herramientas, ajustes de usuario y localización adicional.
**Cierre:** prototipo visual aprobado y pruebas de usabilidad con usuarios.

## Etapa 10 — Seguridad, beta y publicación
- [x] Cabeceras de seguridad HTTP, CSP, no-sniff, no-referrer, frame denial y permisos de cámara limitados.
- [x] Validación de identificadores de proyecto en rutas API y no-cache para respuestas API.
- [ ] Auditoría de dependencias/licencias, privacidad, permisos y retención.
- [x] Base de autenticación/autorización opcional, aislamiento por proyecto, cuotas y borrado de cuenta.
- [ ] HTTPS/gateway, rotación de claves, rate limiting, auditoría de dependencias/licencias y protección antiabuso/costos.
- [ ] Política final de privacidad, retención, consentimiento, backups y recuperación.
- [ ] Pruebas Android/iOS/PWA, rendimiento, batería, red, accesibilidad y recuperación.
- [ ] Beta cerrada, métricas de errores/uso con consentimiento, correcciones y checklist de tiendas.
- [ ] Publicación escalonada solo con autorización expresa.
**Cierre:** checklist aprobado, beta estable y publicación autorizada.

## Reglas de avance
- No declarar una etapa completa si depende de hardware, fotos, medidas o credenciales que no están disponibles.
- Se puede desarrollar en paralelo lo que no dependa de esos insumos, pero conservar las dependencias.
- No simular reconstrucción ni precisión física.
- Los artefactos se guardan en GitHub; las pruebas y su commit se verifican en Actions.
- El lanzamiento público requiere aprobación expresa.
