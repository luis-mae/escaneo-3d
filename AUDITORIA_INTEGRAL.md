# Auditoría integral de Escaneo3D
Fecha: 2026-11-14
Repositorio: luis-mae/escaneo-3d, rama main
Commit auditado: ea8df3c3ebd2a90a99be4891bc36019b1c572320

## Actualización tras las primeras correcciones (14/11/2026)
- CI recuperado: 290 pruebas aprobadas en ejecución completa (commit `9c7368f`); se corrigieron dependencias y errores que impedían la colección/ejecución.
- Se corrigió el cierre de agujeros STL (`usados`), imports de `SimpleNamespace` y la prueba de fusión para comparar geometría invariante a rotación.
- Se añadieron `requirements-dev.txt`, ejecución pytest en GitHub Actions y cinco pruebas iniciales de API; después se ampliaron pruebas de recuperación y orden cronológico.
- API: ahora verifica que el contenido sea realmente JPG/PNG y limita resolución a 100 MP.
- Frontend: se aclaró la diferencia entre manifiesto local y envío al servidor; se alinearon formatos admitidos.
- Se añadió `.gitignore` y se eliminaron 130 artefactos de caché/bytecode versionados.
- Se registran fechas de creación y el listado ordena los proyectos cronológicamente.

## Dictamen ejecutivo
El repositorio contiene una base técnica amplia: herramientas de análisis y reconstrucción experimental, utilidades de mallas, adaptador COLMAP, API local FastAPI, interfaz web y una suite extensa de pruebas. Sin embargo, NO está listo para publicarse ni puede considerarse funcional de extremo a extremo. La afirmación de 125/125 describe el cierre de una secuencia de tareas documentadas, no el cumplimiento de los criterios de aceptación del producto.

## Hallazgos críticos
1. **CI completamente rojo.** GitHub Actions ejecutó 242 pruebas con 2 fallos y 15 errores. Entre ellos: dependencia pytest ausente en CI, importación incorrecta de SimpleNamespace desde unittest.mock, NameError (usadas) en tools/reparar_malla.py y fallos de expectativas/validación en pruebas de fusión y PLY. La suite no puede considerarse aprobada.
2. **Interfaz y backend desincronizados.** web/index.html todavía se presenta como etapa 119 y afirma que las fotos no se envían al servidor; web/app.js ya incorpora un botón que sí las envía. El atributo accept permite WebP, pero JavaScript y API rechazan WebP. Hay dos acciones paralelas que pueden confundir.
3. **Recuperación incompleta.** Se persisten estados, pero no se reanudan trabajos interrumpidos. El listado se reconstruye con glob sin orden cronológico garantizado y el frontend selecciona el último elemento como si fuera el más reciente. Los hilos daemon pueden perder el trabajo al detenerse el servidor.
4. **No hay reconstrucción densa en el flujo web.** pipeline_colmap se invoca con denso=False por defecto. La salida primaria es SfM dispersa (nube PLY); luego se intenta generar una superficie OBJ experimental. No equivale a una malla densa y completa de la pieza.
5. **API no apta para Internet.** No tiene autenticación/autorización, separación por usuario, rate limiting, cuotas, cancelación, cola robusta, protección contra abuso ni retención automática. El módulo advierte que es solo local. No desplegar públicamente ni exponer el puerto.

## Hallazgos importantes
6. Validación de cargas insuficiente: se confía en Content-Type declarado por el cliente, sin inspección de firma/contenido real.
7. Concurrencia: la protección de estado no constituye un gestor de trabajos. Hay ventanas de carrera entre comprobaciones, hilos, borrado y escrituras; no hay límites de concurrencia ni aislamiento de procesos COLMAP.
8. Exportaciones limitadas: la API ofrece OBJ/PLY/STL desde una malla OBJ experimental. No ofrece GLB/3MF/STEP en este flujo. STL no contiene unidades.
9. Escala y precisión: COLMAP produce escala arbitraria sin referencia métrica. No hay ensayos documentados con piezas patrón, tolerancias ni repetibilidad.
10. Documentación inconsistente: README declara estado planificación; ESTADO.md declara 21%; web/index.html sigue en etapa 119; AVANCE_125 aclara que no hubo pruebas integrales.
11. Higiene: hay __pycache__, .pyc y .pytest_cache versionados. Eliminarlos y añadir .gitignore.
12. Pruebas insuficientes: CI solo instala requirements.txt y ejecuta unittest. No instala dependencias web ni pytest, y no prueba API, persistencia, recuperación, borrado, navegador ni COLMAP real.
13. Producto incompleto: no hay evidencia de pruebas Android/iOS, motor local FREE integrado, autenticación, arquitectura PRO remota, métricas/costos ni controles comerciales.

## Aspectos positivos
- Separación de herramientas experimentales con informes y advertencias explícitas.
- Adaptador COLMAP con timeout, comprobación de ejecutable y registro de pasos.
- Límites iniciales de carga por cantidad y tamaño.
- Persistencia atómica del estado.
- Rutas de descarga por identificador y eliminación con confirmación.
- Documentación que evita prometer CAD o precisión industrial.

## Plan de corrección priorizado
### P0 — Integridad
- Corregir CI: instalar pytest y ejecutar pytest (o migrar consistentemente a unittest); arreglar todos los fallos y exigir CI verde.
- Corregir tools/reparar_malla.py y los tests de fusión/PLY.
- Unificar interfaz: una sola acción principal, textos correctos y tipos admitidos coherentes.
- Agregar pruebas FastAPI para alta, límites, MIME/contenido, estados, descarga, borrado, reinicio y concurrencia.
### P1 — Reconstrucción
- Decidir si el producto ofrece nube dispersa o reconstrucción densa; integrar y probar fase densa si se promete malla real.
- Verificar OBJ con objetos reales, topología, huecos, normales y exportación en Blender/FreeCAD/slicer.
- Diferenciar nube dispersa, nube densa y malla en estados e informes.
### P2 — Operación
- Sustituir hilos daemon por cola persistente con exclusión mutua, reintentos, cancelación y límites.
- Ordenar proyectos con timestamps explícitos y recuperar selección determinísticamente.
- Añadir retención configurable, límites de disco y manejo de fallos parciales.
### P3 — Seguridad y producto
- Mantener API local hasta implementar autenticación, autorización, aislamiento y protección de cargas.
- Diseñar backend remoto seguro antes de despliegue público.
- Validar Android/iOS, privacidad, escala y precisión con piezas patrón.
- Actualizar README, ESTADO, plan y criterios de aceptación.

## Conclusión
Estado recomendado: **PROTOTIPO TÉCNICO AVANZADO — NO VALIDADO / NO PUBLICABLE**.
Prioridad inmediata: arreglar CI y el flujo web/API; después ejecutar una reconstrucción real con COLMAP sobre fotografías de una pieza conocida. No publicar ni cobrar hasta superar esos hitos.