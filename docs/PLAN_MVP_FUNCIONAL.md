# PLAN MVP — PRIMERO UN ESCANEO REAL (14/11/2026)

Este plan sustituye las prioridades de ampliación de producto hasta lograr una prueba verificable. No implica que el producto esté terminado.

## Criterio de éxito obligatorio
Desde un teléfono, seleccionar entre 10 y 30 fotos de un objeto real, subirlas a una instancia accesible de la PWA, iniciar COLMAP, consultar el progreso, obtener una nube PLY, visualizar el resultado y descargarlo. Una nube dispersa es aceptable para el primer MVP; no prometer malla cerrada ni escala física.

## Orden de ejecución, con evidencia
1. **Abrir**: levantar el servidor FastAPI existente y verificar `GET /api/salud`, HTML y JavaScript desde un navegador.
2. **Capturar**: seleccionar 10–30 fotos JPEG/PNG desde móvil; revisar que el contador, los tamaños y la subida funcionan.
3. **Procesar**: ejecutar COLMAP real en el host, con logs y errores visibles; no confundir un mock con prueba real.
4. **Recuperar**: consultar el proyecto hasta `completado`; comprobar que se generó un PLY no vacío.
5. **Visualizar**: abrir la nube/malla en el visor; si el visor solo admite OBJ, convertir la nube a malla y registrar el fallo cuando no sea posible.
6. **Exportar**: descargar PLY u OBJ generado por la ejecución real y abrirlo con una herramienta independiente.
7. **Acceso móvil**: publicar únicamente la PWA contra un backend aislado con HTTPS y autenticación; nunca exponer la API local sin protección.

## Regla de evidencia
Cada paso debe tener: comando/acción reproducible, resultado observado y prueba concreta. Si no se ejecutó, escribir **NO VERIFICADO**. Los commits y porcentajes no equivalen a funcionamiento.

## Se pospone
Planes, pagos, suscripciones, cuotas comerciales, trabajadores distribuidos, STEP/IGES/DXF, precisión certificada, estética definitiva y aplicaciones nativas.

## Estado inicial honesto
Existe código para API, carga de fotografías, COLMAP, visor y exportación. **No hay evidencia en este documento de una reconstrucción real completa ejecutada hoy ni de una URL pública funcional**. El despliegue, las pruebas reales y la validación móvil están pendientes.
