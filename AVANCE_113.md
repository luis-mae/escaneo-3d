# Etapa 113 — Pipeline COLMAP integrado

Se incorporó `tools/pipeline_colmap.py` como entrada única para ejecutar SfM disperso y, opcionalmente, reconstrucción densa con COLMAP instalado en el equipo. Produce `pipeline_colmap.json` y conserva resultados dispersos si falla la densificación.

```bash
python -m tools.pipeline_colmap carpeta_fotos --salida resultado_colmap
python -m tools.pipeline_colmap carpeta_fotos --salida resultado_colmap_nuevo --denso
```

La segunda opción puede requerir GPU NVIDIA/CUDA. Se añadieron pruebas simuladas de ejecución, fallo denso y ejecución sin fase densa. **Pendientes:** ejecutar CI, instalar/ejecutar COLMAP en un entorno compatible, validar imágenes reales y desarrollar malla superficial. No hay escala física garantizada.
