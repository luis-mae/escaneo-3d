# Etapa 115 — Reconstrucción automática de superficies

Implementado `tools/superficie_automatica.py`: lee nube PLY de COLMAP, limita cantidad de puntos por muestreo determinista, estima espaciamiento local con KD-tree y prueba radios alpha crecientes para producir una malla OBJ usando el mallador existente. Prioriza el primer resultado cerrado por aristas si se encuentra; genera diagnóstico JSON con parámetros, intentos y topología. No sobrescribe archivos existentes.

```bash
python -m tools.superficie_automatica resultado_colmap/dense_0/fused.ply --salida modelo.obj
```

Se agregaron pruebas unitarias; **todavía no se ejecutaron pruebas reales ni se validó CI**. El mallado alpha puede generar superficies defectuosas y no garantiza escala física, cierre geométrico ni impresión 3D. Próxima etapa: reparación de mallas.
