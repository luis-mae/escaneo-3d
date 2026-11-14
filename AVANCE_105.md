# Etapa 105 — Fotografías → tracks → SfM incremental → PLY

Se añadió `tools/fotos_a_nube_global.py`, un comando integrado que lee fotografías de igual resolución, calcula tracks ORB, ejecuta SfM incremental experimental y exporta nube PLY, tracks JSON e informe con hashes SHA-256. Rechaza imágenes duplicadas, ilegibles o de distinta resolución, reconstrucciones insuficientes y archivos de salida preexistentes.

Ejemplo:

```bash
python -m tools.fotos_a_nube_global foto1.jpg foto2.jpg foto3.jpg --focal-px 1200 --salida resultado_sfm
```

Pruebas de integración añadidas con simulación de tracks/SfM. **No verificadas en CI**; falta comprobar imágenes reales, robustez de registro, ajuste multivista, escala métrica y calidad de superficie. La salida es una nube dispersa experimental, no un modelo imprimible.
