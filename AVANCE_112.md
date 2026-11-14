# Etapa 112 — Reconstrucción densa con COLMAP

Se incorporó `tools/colmap_denso.py`, que utiliza las salidas SfM de COLMAP para ejecutar `image_undistorter`, `patch_match_stereo` y `stereo_fusion`, generando `dense_0/fused.ply` e `informe_denso.json`. Incluye protección contra sobrescritura, validación de entradas, control de tiempos y registro de errores. Pruebas simuladas añadidas.

Ejemplo, tras completar la reconstrucción dispersa:

```bash
python -m tools.colmap_denso resultado_colmap carpeta_fotos --modelo 0
```

**Requisitos:** COLMAP instalado y, habitualmente, GPU NVIDIA/CUDA para PatchMatch; la disponibilidad depende de la compilación. **No se ejecutó aún en hardware real ni se verificó CI.** El resultado es una nube densa, no una malla cerrada ni una reconstrucción de escala física.
