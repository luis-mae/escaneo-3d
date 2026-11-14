# Escaneo3D

Aplicación para capturar objetos pequeños mediante fotografías y transformarlos en modelos 3D, con prioridad en repuestos y piezas para fabricación. Objetivo: Android, iOS y PWA, con código compartido donde sea viable.

**Estado actual (14/11/2026):** prototipo técnico avanzado, todavía no validado para publicación. La hoja de ruta de producto vigente tiene diez etapas y está en `docs/ROADMAP_10_ETAPAS.md`. Incluye herramientas experimentales de geometría, adaptador COLMAP, API local FastAPI, PWA móvil, biblioteca local de proyectos y flujo de exportación OBJ/PLY/STL seleccionado por el usuario. El flujo web puede solicitar reconstrucción dispersa y, opcionalmente, densa (PatchMatch Stereo; puede requerir GPU). Si la fase densa falla, conserva la nube dispersa cuando está disponible. La malla alpha-shape usa submuestreo determinista acotado y un alpha heurístico basado en el espaciamiento local; sigue siendo experimental y la escala no está certificada. No publicar ni exponer la API a Internet.

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

### PWA y captura móvil
La interfaz incorpora manifiesto instalable, icono, caché offline de la carcasa visual (sin cachear API ni datos personales), captura de fotografías con la cámara trasera, selección y eliminación individual de fotos, biblioteca local de proyectos con apertura y renombrado. No reemplaza todavía una aplicación nativa ni permite reconstruir sin conexión.

### Guardar o exportar a…
Al terminar la malla, la persona elige STL para impresión 3D, OBJ para intercambio/edición de mallas y PLY para nube o malla. Solo se generan los formatos seleccionados. GLB, 3MF y CAD se muestran como próximos porque requieren conversores reales; no se simula una conversión cambiando extensiones. La escala sigue sin verificarse salvo calibración independiente.

### Visor 3D interactivo (experimental)
Al completar la generación OBJ aparece «Ver modelo 3D». El visor local permite rotar con arrastre o flechas, acercar con rueda o teclas +/- y restablecer la vista con doble clic o Inicio. Para mantener fluidez, simplifica visualmente mallas superiores a 18.000 caras y limita la carga a 500.000 vértices/caras. Muestra una caja envolvente en unidades relativas, permite descargar el informe topológico y ofrece un ZIP con los resultados generados, un manifiesto SHA-256 y advertencias (sin incluir fotografías originales). Es una previsualización, no mide dimensiones físicas ni certifica geometría.

### Reconstrucción densa opcional
En la interfaz, activar «Intentar reconstrucción densa» solicita COLMAP `image_undistorter`, `patch_match_stereo` y `stereo_fusion`. Puede fallar en equipos sin CUDA o con recursos insuficientes; en ese caso se conserva el resultado disperso. La opción no promete una malla cerrada ni precisión dimensional.

La generación de malla limita la triangulación a 50.000 puntos mediante submuestreo determinista cuando la nube supera ese tamaño. El alpha automático se estima como tres veces la mediana de distancia al vecino más próximo en la muestra. La interfaz permite introducir un alpha manual si se necesita ajustar el resultado. Es una heurística de inicialización, no una garantía geométrica; se debe inspeccionar el OBJ.

## Estado de calidad
- CI: la ejecución del commit `9878bf9` aprobó 336 pruebas, 1 warning y 8 subtests; validación de sintaxis y prueba funcional del visor aprobadas.
- API: solo para uso local y de confianza; sin autenticación ni aislamiento multiusuario.
- Validación real: pendiente con fotografías de piezas conocidas, reconstrucción densa y comparación dimensional.
- PWA y captura móvil: base implementada; aplicación nativa, guía de recorrido y revisión de tomas pendientes.
- Biblioteca de proyectos: selección y reapertura local implementadas; sincronización multiusuario pendiente.
- Seguridad, backend remoto, cuentas, pagos, dispositivos nativos y costos: pendientes antes de cualquier lanzamiento.

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
