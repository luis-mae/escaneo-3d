# Escaneo3D

Aplicación para capturar objetos pequeños mediante fotografías y transformarlos en modelos 3D, con prioridad en repuestos y piezas para fabricación. Objetivo: Android, iOS y PWA, con código compartido donde sea viable.

**Estado actual (14/11/2026):** prototipo técnico avanzado, todavía no validado para publicación. La hoja de ruta de producto vigente tiene diez etapas y está en `docs/ROADMAP_10_ETAPAS.md`. Incluye herramientas experimentales de geometría, adaptador COLMAP, API local FastAPI, PWA móvil, biblioteca local de proyectos y flujo de exportación OBJ/PLY/STL/GLB seleccionado por el usuario. El flujo web puede solicitar reconstrucción dispersa y, opcionalmente, densa (PatchMatch Stereo; puede requerir GPU). Si la fase densa falla, conserva la nube dispersa cuando está disponible. La malla alpha-shape usa submuestreo determinista acotado y un alpha heurístico basado en el espaciamiento local; sigue siendo experimental y la escala no está certificada. No publicar ni exponer la API a Internet.

## Principios
- FREE: procesamiento local cuando el dispositivo sea compatible; privacidad y exportación útil.
- PLUS: más trabajos locales por mes.
- PRO: procesamiento externo/híbrido, más trabajos y reconstrucción avanzada.
- Cuotas preliminares: FREE 5, PLUS 25, PRO 50 escaneos/mes; precios sujetos a costos medidos.
- La precisión dimensional exige referencia de escala y validación; no prometer tolerancias industriales.
- La exportación de mallas no equivale a CAD paramétrico.
- No publicar ni activar cobros antes de pruebas funcionales, de costos y privacidad.

### Ejecutar en contenedor (Docker)
Requiere Docker Engine y el complemento Docker Compose. Desde la raíz del repositorio:
```bash
docker compose up --build -d
```
Abrí `http://127.0.0.1:8000`. Los proyectos quedan en el volumen persistente `escaneo3d_data` administrado por Docker. Para detener: `docker compose down`; para borrar también los proyectos: `docker compose down -v` (acción destructiva). El puerto queda enlazado exclusivamente a localhost. La imagen instala COLMAP y dependencias CPU; no presupone disponibilidad CUDA/GPU.

### Ejecutar el prototipo web local
Instalá dependencias con `python -m pip install -r requirements-web.txt` y ejecutá `python -m uvicorn tools.servidor_web:app --host 127.0.0.1 --port 8000`. Abrí `http://127.0.0.1:8000`. COLMAP debe estar instalado y disponible en `PATH`. La API no tiene autenticación: mantené `127.0.0.1`, no la expongas a una red pública. El servidor limita la cola a tres proyectos y serializa las tareas pesadas para reducir picos de CPU y memoria. Añade cabeceras de seguridad, Content Security Policy, validación de identificadores y respuestas API sin caché.

### Guía de uso y privacidad
La interfaz incluye una guía rápida de captura y exportación y una página de privacidad que describe dónde se almacenan las fotos, cómo borrar proyectos y los límites del prototipo. La carga al servidor exige marcar un consentimiento explícito.

### PWA y captura móvil
La captura incluye un recorrido orientativo de 20 tomas (12 horizontales y 8 elevadas), con instrucciones por posición y revisión/eliminación individual antes del envío. La guía es orientativa y no detecta por sí sola cobertura real ni desenfoque en tiempo de captura.
La interfaz incorpora manifiesto instalable, icono, caché offline de la carcasa visual (sin cachear API ni datos personales), captura de fotografías con la cámara trasera, selección y eliminación individual de fotos, biblioteca local de proyectos con apertura y renombrado. No reemplaza todavía una aplicación nativa ni permite reconstruir sin conexión.

### Guardar o exportar a…
Al terminar la malla, la persona elige STL para impresión 3D, OBJ para intercambio/edición de mallas, PLY de malla, nube PLY original de COLMAP y GLB 2.0 para visores web y aplicaciones compatibles. GLB exporta geometría triangular sin materiales ni texturas; las unidades siguen sin verificarse. Solo se generan los formatos seleccionados. GLB 2.0 y 3MF Core se exportan con geometría triangular real; 3MF asume milímetros y requiere calibración física para obtener dimensiones fiables. STEP, IGES y DXF continúan pendientes porque requieren conversión CAD específica. La escala sigue sin verificarse salvo calibración independiente.

### Biblioteca de proyectos
La biblioteca permite reabrir, renombrar, duplicar y eliminar proyectos desde la interfaz. La duplicación crea una copia independiente de fotos y resultados; no duplica proyectos mientras hay procesos activos.

### Visor 3D interactivo (experimental)
Al completar la generación OBJ aparece «Ver modelo 3D». El visor local permite rotar con arrastre o flechas, acercar con rueda o teclas +/- y restablecer la vista con doble clic o Inicio. Para mantener fluidez, simplifica visualmente mallas superiores a 18.000 caras y limita la carga a 500.000 vértices/caras. Muestra una caja envolvente en unidades relativas, permite descargar el informe topológico y ofrece un ZIP con los resultados generados, un manifiesto SHA-256 y advertencias (sin incluir fotografías originales). Es una previsualización, no mide dimensiones físicas ni certifica geometría.

### Reconstrucción densa opcional
En la interfaz, activar «Intentar reconstrucción densa» solicita COLMAP `image_undistorter`, `patch_match_stereo` y `stereo_fusion`. Puede fallar en equipos sin CUDA o con recursos insuficientes; en ese caso se conserva el resultado disperso. La opción no promete una malla cerrada ni precisión dimensional.

La generación de malla limita la triangulación a 50.000 puntos mediante submuestreo determinista cuando la nube supera ese tamaño. El alpha automático se estima como tres veces la mediana de distancia al vecino más próximo en la muestra. La interfaz permite introducir un alpha manual si se necesita ajustar el resultado. Es una heurística de inicialización, no una garantía geométrica; se debe inspeccionar el OBJ.

## Estado de calidad
- CI: la ejecución del commit `9878bf9` aprobó 336 pruebas, 1 warning y 8 subtests; validación de sintaxis y prueba funcional del visor aprobadas.
- API: solo para uso local y de confianza; sin autenticación ni aislamiento multiusuario. La interfaz exige consentimiento de subida y publica información técnica de privacidad, pero esto no sustituye las medidas legales y de seguridad de un servicio público.
- Validación real: pendiente con fotografías de piezas conocidas, reconstrucción densa y comparación dimensional.
- PWA y captura móvil: base implementada con recorrido orientativo y revisión individual; aplicación nativa y análisis de captura en tiempo real pendientes.
- Biblioteca de proyectos: selección, reapertura, renombrado, duplicación y eliminación local implementados; sincronización multiusuario pendiente.
- El motor COLMAP aplica un presupuesto global de tiempo compartido entre fases dispersa, conversión y densa.
- El motor SQLite de cuotas FREE/PLUS/PRO está desarrollado como módulo base, aún sin vincular a identidad ni pagos.
- Seguridad, backend remoto multiusuario, proveedor de pagos, dispositivos nativos y costos: pendientes antes de cualquier lanzamiento.

## Etapas
Ver [hoja de ruta de diez etapas](docs/ROADMAP_10_ETAPAS.md), [criterios de aceptación](docs/CRITERIOS_DE_ACEPTACION.md) y [protocolo de validación real](docs/PROTOCOLO_VALIDACION_REAL.md).

### Preflight de captura (etapa 1)
Al recibir las fotografías, el servidor genera `informe_captura.json` y muestra un resumen de resolución, exposición, detalle aproximado y posibles duplicados. El informe se puede descargar desde el proyecto. Es una ayuda heurística: no descarta imágenes automáticamente ni garantiza que COLMAP pueda reconstruirlas.

### Herramienta de orientación STL (experimental)
`python tools/orientar_stl.py entrada.stl salida.stl` intenta orientar consistentemente las caras y, para componentes cerrados, hacia afuera. Reporta componentes abiertos, conflictos y aristas no manifold. No repara la malla ni certifica que sea imprimible.

### Preparación de fotografías (experimental)

`python tools/preparar_fotografias.py fotos_originales fotos_preparadas --max-lado 2048`

Requiere `Pillow`. Genera copias JPEG orientadas y un `manifest.json` sin modificar originales. No constituye un motor de fotogrametría.

### Superficie no convexa experimental (avance 61)

`python tools/superficie_concava.py nube.json --alpha 0.5 --salida superficie.obj`

El algoritmo alpha-shape 3D filtra tetraedros de Delaunay por radio de circunsfera y extrae su frontera. A diferencia de la envolvente convexa, puede representar algunas concavidades, dependiendo de la densidad de puntos y del parámetro `alpha`. No garantiza malla cerrada ni fotogrametría funcional de extremo a extremo. Las unidades dependen de la escala de entrada.

### Pipeline nube a superficie e informe (avance 65)

`python -m tools.pipeline_superficie nube.json --alpha 0.5 --salida modelo.obj`

Genera `modelo.obj` y `modelo.informe.json` con aristas abiertas/no manifold.
**Requiere** una nube 3D ya reconstruida; no estima cámaras ni reconstruye
fotografías automáticamente. Un informe sin aristas abiertas **no certifica**
que la malla sea imprimible, correcta o esté escalada.

### Tracks a partir de fotografías (avance 74)

`python -m tools.tracks_desde_fotos foto01.jpg foto02.jpg foto03.jpg --salida tracks.json`

Requiere OpenCV y NumPy. Extrae puntos ORB y correspondencias geométricamente filtradas. El JSON sirve como entrada parcial a los pipelines multivista, pero **no incluye poses de cámara** ni genera por sí solo una nube 3D. La validación con fotografías reales está pendiente.

### Avance 77: calibración métrica opcional de nubes PLY

`python -m tools.escala_metrica nube.ply --punto-a 0 0 0 --punto-b 2 0 0 --distancia-mm 50 --salida nube_mm.ply`

Los puntos de referencia se expresan en las coordenadas de la nube original y deben representar una distancia real conocida. Produce un nuevo PLY ASCII en milímetros y un informe JSON. **No corrige la deriva de escala entre pares de fotos, ni reemplaza la calibración de cámara o una reconstrucción SfM robusta.**

## Análisis dimensional para validación real\n\nCon mediciones físicas y medidas tomadas sobre el modelo ya calibrado, generar un informe de error con `python -m tools.informe_validacion mediciones.json --tolerancia-pct 5 --salida informe.json`. La herramienta no mide el modelo ni certifica precisión: analiza datos medidos por el operador. Ver [protocolo de validación real](docs/PROTOCOLO_VALIDACION_REAL.md).\n\n## Verificación del paquete de resultados\n\nDespués de descargar `escaneo3d_resultados.zip`, verificar su integridad y que no contenga imágenes con:\n\n`python -m tools.verificar_paquete escaneo3d_resultados.zip`\n\nEl verificador comprueba el manifiesto SHA-256, tamaños, rutas relativas y ausencia de archivos de imagen.\n\n## Avance 78: control de escala métrica
Se agregó tools/calibracion_metrica.py: valida al menos dos distancias físicas independientes, detecta escalas incompatibles y bloquea la conversión a milímetros si falla. No resuelve la escala variable entre poses ni valida la reconstrucción con fotos reales.


### Modo remoto autenticado (base de integración)

El backend incorpora una barrera JWT HS256 opcional, aislamiento de proyectos por `sub` y consulta de cuota del usuario autenticado. Para activarla, configurar obligatoriamente:

- `ESCANEO3D_AUTH_REQUIRED=1`
- `ESCANEO3D_JWT_SECRET`: secreto aleatorio de al menos 32 bytes, compartido de forma segura con el emisor.
- `ESCANEO3D_JWT_ISSUER`: valor exacto de `iss`.
- `ESCANEO3D_JWT_AUDIENCE`: audiencia exacta incluida en `aud`.

El token debe usar HS256, incluir `sub`, `iss`, `aud` y `exp`; se validan firma, vencimiento, emisor y audiencia. La vigencia máxima aceptada es 24 horas. No se emiten tokens desde esta aplicación: se necesita un proveedor de identidad o gateway seguro que los emita. La PWA aún requiere integrar el inicio de sesión y el envío del bearer token antes de usar el modo remoto.

En modo autenticado, los proyectos se aíslan por subject y la cuota se reserva al iniciar la reconstrucción; se consume al completar y se libera si el procesamiento falla. Consultar `GET /api/cuenta/entitlements` para conocer el plan y el saldo. La cuenta debe provisionarse previamente desde consola:

```bash
python -m tools.admin_cuenta usuario-subject --plan FREE
```

Los valores FREE 5, PLUS 25 y PRO 50 son cuotas de desarrollo configurables, no precios ni oferta comercial. No hay checkout ni suscripciones integrados todavía. No activar el modo remoto sin un emisor JWT seguro, HTTPS, almacenamiento privado y despliegue aislado; el modo local sigue siendo el predeterminado.


En modo autenticado, `DELETE /api/cuenta` elimina los proyectos y archivos del usuario y sus registros de cuota; el servidor rechaza el borrado si hay trabajos activos. La eliminación de identidad en el proveedor externo debe coordinarse por separado.


### Calibración de escala desde el visor
El visor permite ingresar dos distancias físicas conocidas y seleccionar sus cuatro extremos sobre la malla. Si los dos factores de escala difieren como máximo un 5%, ofrece copias OBJ y STL expresadas en milímetros y un informe JSON. La generación de STL se bloquea si encuentra triángulos degenerados. Es una calibración global orientativa: no corrige deriva de cámara ni deformaciones locales. Verificá una tercera medida independiente y no interpretes una malla cerrada como garantía de imprimibilidad.

El visor también permite seleccionar dos vértices y calcular una distancia aproximada después de calibrar la escala. No reemplaza un instrumento metrológico ni informa incertidumbre certificada.


### Cancelar una reconstrucción
Mientras COLMAP está en cola o ejecutándose, la interfaz muestra **Cancelar reconstrucción**. La API marca la solicitud, termina el subproceso activo (con terminación forzada si no responde) y deja el proyecto en estado `cancelado`. Si había una reserva de cuota, se libera. La cancelación no elimina las fotografías ni los resultados parciales: el usuario puede borrar el proyecto cuando el proceso haya terminado.

Si una reconstrucción falla, se cancela o queda interrumpida tras un reinicio, la interfaz ofrece **Reintentar reconstrucción**. El reintento conserva las fotografías originales, limpia los resultados parciales y reserva una nueva unidad de cuota; no se ejecutan reintentos automáticos que puedan consumir recursos sin autorización.
