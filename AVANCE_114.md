# Etapa 114 — Nube COLMAP a superficie

Implementado lector PLY ASCII/binario (`tools/leer_colmap_ply.py`) con propiedades XYZ y canales adicionales, límites de tamaño y validaciones de formato. Implementado puente `tools/colmap_a_malla.py` que reutiliza `pipeline_superficie.procesar` (alpha-shape) y exporta OBJ con informe de aristas y advertencias.

```bash
python -m tools.colmap_a_malla resultado_colmap/dense_0/fused.ply --alpha 0.1 --salida resultado_colmap/malla.obj
```

El parámetro alpha depende de la escala arbitraria y densidad de la nube. Para nubes grandes puede requerirse reducción previa. La malla es experimental; **no se ha validado con fotografías reales ni se certifica impresión 3D**. Se agregaron pruebas simuladas, todavía sin ejecutar en CI.
