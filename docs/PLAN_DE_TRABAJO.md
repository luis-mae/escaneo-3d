# Plan de trabajo por etapas — Escaneo3D

Los porcentajes son pesos de planificación, no avances realizados. Cada etapa requiere evidencia verificable antes de cerrarse.

## 1. Repositorio y planificación (5%)
- Crear repositorio GitHub `luis-mae/escaneo`, preferentemente privado inicialmente.
- Incorporar README, este plan, criterios de aceptación, licencia a decidir y registro de decisiones.
- Definir ramas `main` y `develop`, protección de secretos, issues y CI inicial.
**Salida:** repositorio accesible y documentos versionados.

## 2. Viabilidad técnica y prototipos (15%)
- Probar reconstrucción local real en al menos un Android y un iPhone; distinguir captura, nube de puntos y malla reconstruida.
- Evaluar límites de memoria, CPU/GPU, batería y PWA; seleccionar motor local o definir compatibilidad restringida.
- Probar backend fotogramétrico (p. ej., COLMAP + OpenMVS) y medir tiempos, costo, calidad y licencias.
- Seleccionar arquitectura: React Native/Expo + web, módulos nativos cuando se requieran, API y cola de trabajos.
**Salida:** informe con demostraciones, matriz de compatibilidad y decisión técnica documentada.

## 3. Captura guiada (12%)
- Cámara con captura manual y automática configurable (~1 foto/segundo), indicador de progreso, guía de ángulos y revisión de tomas.
- Opcional: video y extracción de fotogramas; verificar calidad y permisos.
- Plantilla imprimible de calibración opcional; alternativa regla/medida conocida; aviso de escala no verificada.
**Salida:** conjunto de fotos reproducible y exportable, con metadatos y consentimiento.

## 4. Reconstrucción FREE local (18%)
- Integrar motor local únicamente en dispositivos compatibles; control de memoria, cancelación y errores.
- Generar malla real; si no es viable, informar claramente incompatibilidad sin simular reconstrucción.
- Definir almacenamiento y borrado local.
**Salida:** objeto de prueba reconstruido sin servidor, medido en dispositivos reales.

## 5. Visor, medidas y exportaciones (12%)
- Visor rotación, zoom, comparación y estado de calidad.
- Exportar STL, OBJ, PLY, GLB y 3MF cuando el formato esté implementado y validado.
- Medidas solo con escala establecida; advertencia de tolerancia e incertidumbre.
- Presets de exportación para Blender, FreeCAD, Fusion, SolidWorks e impresión 3D, según compatibilidad real.
**Salida:** archivos abiertos con éxito en herramientas destino y modelos de prueba documentados.

## 6. Reconstrucción PRO híbrida (15%)
- Subida cifrada y autorizada de imágenes, cola, procesamiento externo, estados, descargas y eliminación.
- Control de costos por trabajo, límites de fotos/resolución/tiempo, reintentos y seguridad.
- Mejoras de malla y validación de calidad frente a FREE; no prometer mayor calidad en todos los casos.
**Salida:** trabajos completos con métricas de costo y resultados reproducibles.

## 7. Ingeniería inversa CAD (8%)
- Conversión básica de mallas entre formatos, sin presentarla como CAD editable.
- Prototipo de detección de planos, cilindros, agujeros y perfiles en piezas simples.
- STEP/IGES genuinos cuando exista reconstrucción de superficies/sólidos; DXF para secciones 2D.
- Declarar claramente los límites de automatización y precisión.
**Salida:** pieza simple exportada y editable en al menos un CAD de referencia.

## 8. Cuentas, cuotas y monetización (7%)
- Cuentas opcionales cuando sean posibles, identificación de trabajos y cuotas mensuales FREE 5 / PLUS 25 / PRO 50.
- Protección antifraude razonable, políticas de reinicio y fallos que no consuman cuota injustamente.
- Medir costo real antes de fijar precios; integrar pagos y suscripciones conforme a políticas de tiendas cuando corresponda.
- Analítica propia con eventos mínimos y consentimiento, complementable con analítica externa.
**Salida:** pruebas de cuotas, compras, cancelaciones y costos.

## 9. Calidad, seguridad y publicación (8%)
- Pruebas Android/iOS/PWA; permisos, accesibilidad, privacidad, eliminación de fotos, fallos de red, uso de batería.
- Tests de geometría, seguridad del backend y límites de archivos; telemetría sin imágenes privadas por defecto.
- Beta cerrada, métricas, correcciones y luego publicación escalonada en tiendas/PWA.
**Salida:** checklist aprobado, beta validada y publicación autorizada expresamente.

## Orden y dependencias
La etapa 2 es una puerta de decisión: no prometer FREE local universal antes de validarla. La etapa 3 puede desarrollarse en paralelo con prototipos. Etapas 5 y 6 dependen de obtener mallas reales. Etapa 8 no activa cobros antes de medir costos de etapa 6. Etapa 9 exige aprobación de lanzamiento.

## Riesgos principales
- Fotogrametría local en teléfonos corrientes puede ser inviable o limitada.
- Superficies reflectantes, transparentes, lisas o piezas muy pequeñas dificultan la reconstrucción.
- Sin escala verificada, dimensiones y fabricación pueden ser inexactas.
- Conversión a STEP no produce automáticamente historial paramétrico.
- Costos de GPU/almacenamiento y comisiones pueden superar ingresos si las cuotas no están controladas.


## Extensión posterior a la versión 1.0

### Etapa 126 — Visor 3D interactivo (implementada; CI aprobada)
- Visualizar OBJ dentro de la interfaz, sin dependencia de servicios externos.
- Rotación por arrastre, zoom y restablecimiento de cámara.
- Limitar consumo de memoria y simplificar la vista para mallas grandes.
- Mostrar recuento de vértices/caras y advertir que la vista no certifica medidas ni imprimibilidad.
**Salida:** visor integrado, accesible desde cada proyecto y cubierto por pruebas automatizadas de carga, render, controles por teclado, caras poligonales e índices negativos. CI: 314 pruebas Python aprobadas; validación sintáctica y funcional del visor aprobada.

### Etapa 127 — Validación geométrica con piezas reales (protocolo preparado; ejecución pendiente)
- Escanear al menos tres objetos de geometría/materiales diferentes y dimensiones conocidas.
- Comparar nube dispersa y densa, malla y exportaciones en un visor/CAD independiente.
- Registrar éxito, tiempo, memoria, densidad, agujeros, componentes, error dimensional y límites.
- Ajustar guía de captura y criterios de calidad con resultados observados.
**Salida:** informe reproducible de validación. No se considera completada sin fotografías y mediciones reales.
