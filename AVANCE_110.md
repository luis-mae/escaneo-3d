# Etapa 110 — COLMAP como prioridad principal

Se incorporó el adaptador `tools/motor_colmap.py` para ejecutar una instalación externa de **COLMAP**, motor gratuito y de código abierto. Ejecuta extracción SIFT, matching exhaustivo y mapper SfM; produce `database.db`, modelos dispersos en `sparse/` e `informe_colmap.json` con resultados y errores. Por defecto usa CPU, sin GPU, y evita sobrescribir resultados.

Uso, **una vez instalado COLMAP en el equipo**:

```bash
python -m tools.motor_colmap carpeta_fotos --salida resultado_colmap
```

Se añadieron pruebas del adaptador, sin ejecutar aún. **COLMAP no está instalado ni ejecutado en el repositorio**; el adaptador es el primer paso de integración. Pendientes prioritarios: ejecución real, pruebas CI, exportación PLY y reconstrucción densa opcional. La nube dispersa carece de escala física.
