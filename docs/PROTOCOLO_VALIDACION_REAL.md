# Protocolo de validación con objetos reales

Este protocolo queda preparado para la etapa 127. No sustituye las pruebas con COLMAP ejecutado sobre fotografías reales.

## Objetivo
Medir si la captura y la reconstrucción producen geometría útil, qué condiciones fallan y cuánto se desvía el resultado de dimensiones conocidas. No se presupone precisión industrial.

## Objetos de prueba
1. **Geometría simple y rígida:** bloque o pieza prismática, con tres dimensiones medidas con calibre.
2. **Geometría con concavidades/agujeros:** soporte o pieza mecánica con al menos un agujero y una cavidad.
3. **Superficie orgánica o irregular:** objeto mate, sin transparencia ni brillo intenso, para evaluar cobertura y textura.

Registrar para cada objeto: material, color, dimensiones de referencia, instrumento de medida, incertidumbre del instrumento, iluminación y fondo.

## Captura
- Limpiar el fondo y mantener el objeto inmóvil.
- Tomar fotografías nítidas con solapamiento alto; recorrer 360° en varias alturas.
- Incluir vistas superiores e inferiores cuando sean accesibles.
- Evitar reflejos, transparencias, desenfoque y cambios de iluminación.
- Guardar originales sin recomprimir y anotar cantidad, resolución y tamaño.
- No mezclar fotografías de distintas sesiones ni cambiar la posición del objeto entre tomas.

## Ejecución
Para cada objeto, crear dos proyectos comparables:
- Reconstrucción dispersa (opción densa desactivada).
- Reconstrucción con intento denso (opción densa activada).

Guardar identificadores, estados, tiempos, mensajes de error, tamaño de archivos y reportes. Si PatchMatch no está disponible, registrar la causa y conservar el resultado disperso como fallback.

## Métricas a registrar
- Fotos cargadas y aceptadas; cobertura visual observada.
- Tiempo de reconstrucción dispersa y densa.
- Cantidad de puntos, vértices y caras.
- Aristas abiertas, aristas no-manifold y componentes desconectados cuando se disponga del dato.
- Caja envolvente de la nube/malla, marcada como unidad relativa hasta calibrar escala.
- Diferencia entre dimensiones exportadas y dimensiones de referencia, solo después de aplicar una referencia de escala conocida.
- Apertura en al menos un visor 3D independiente y revisión de OBJ, PLY y STL.
- Fallos, artefactos, zonas ausentes y superficies reconstruidas incorrectamente.

## Criterios de interpretación
- Una nube densa no implica una malla cerrada.
- Una malla cerrada por aristas no implica que la superficie sea correcta ni imprimible.
- Un STL exportado no certifica unidades, tolerancias ni aptitud de fabricación.
- No declarar precisión dimensional hasta comparar varias distancias independientes con mediciones físicas.
- Conservar fotos, parámetros, informes y archivos de salida para que la prueba sea repetible.

## Resultado esperado
Un informe por objeto con fotografías de referencia, configuración, métricas, archivos generados, problemas y conclusión. La etapa 127 solo se cierra cuando se hayan realizado y documentado pruebas físicas reales.
