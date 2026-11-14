# Escaneo3D

Aplicación para capturar objetos pequeños mediante fotografías y transformarlos en modelos 3D, con prioridad en repuestos y piezas para fabricación. Objetivo: Android, iOS y PWA, con código compartido donde sea viable.

**Estado actual (14/11/2026):** prototipo técnico avanzado, todavía no validado para publicación. Incluye herramientas experimentales de geometría, adaptador COLMAP, API local FastAPI, interfaz web y exportación OBJ/PLY/STL. El flujo web puede solicitar reconstrucción dispersa y, opcionalmente, densa (PatchMatch Stereo; puede requerir GPU). Si la fase densa falla, conserva la nube dispersa cuando está disponible. La malla alpha-shape usa submuestreo determinista acotado y un alpha heurístico basado en el espaciamiento local; sigue siendo experimental y la escala no está certificada. No publicar ni exponer la API a Internet.

## Principios
- FREE: procesamiento local cuando el dispositivo sea compatible; privacidad y exportación útil.
- PLUS: más trabajos locales por mes.
- PRO: procesamiento externo/híbrido, más trabajos y reconstrucción avanzada.
- Cuotas preliminares: FREE 5, PLUS 25, PRO 50 escaneos/mes; precios sujetos a costos medidos.
- La precisión dimensional exige referencia de escala y validación; no prometer tolerancias industriales.
- La exportación de mallas no equivale a CAD paramétrico.
- No publicar ni activar cobros antes de pruebas funcionales, de costos y privacidad.

### Ejecutar el prototipo web local
Instalá dependencias con `python -m pip install -r requirements-web.txt` y ejecutá `python -m uvicorn tools.servidor_web:app --host 127.0.0.1 --port 8000`. Abrí `http://127.0.0.1:8000`. COLMAP debe estar instalado y disponible en `PATH`. La API no tiene autenticación: mantené `127.0.0.1`, no la expongas a una red pública.

### Reconstrucción densa opcional
En la interfaz, activar «Intentar reconstrucción densa» solicita COLMAP `image_undistorter`, `patch_match_stereo` y `stereo_fusion`. Puede fallar en equipos sin CUDA o con recursos insuficientes; en ese caso se conserva el resultado disperso. La opción no promete una malla cerrada ni precisión dimensional.

La generación de malla limita la triangulación a 50.000 puntos mediante submuestreo determinista cuando la nube supera ese tamaño. El alpha automático se estima como tres veces la mediana de distancia al vecino más próximo en la muestra. Es una heurística de inicialización, no una garantía geométrica; se debe inspeccionar el OBJ.

## Estado de calidad
- CI: 290 pruebas aprobadas en la última ejecución completa observada (14/11/2026); repetir tras los últimos cambios de limpieza del repositorio.
- API: solo para uso local y de confianza; sin autenticación ni aislamiento multiusuario.
- Validación real: pendiente con fotografías de piezas conocidas, reconstrucción densa y comparación dimensional.
- Seguridad, dispositivos móviles y costos: pendientes antes de cualquier lanzamiento.

## Etapas
Ver [PLAN_DE_TRABAJO.md](docs/PLAN_DE_TRABAJO.md) y [CRITERIOS_DE_ACEPTACION.md](docs/CRITERIOS_DE_ACEPTACION.md).

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

## Avance 78: control de escala métrica
Se agregó tools/calibracion_metrica.py: valida al menos dos distancias físicas independientes, detecta escalas incompatibles y bloquea la conversión a milímetros si falla. No resuelve la escala variable entre poses ni valida la reconstrucción con fotos reales.
