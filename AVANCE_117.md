# Etapa 117 — Optimización y suavizado

Se aprovechó el optimizador STL ya presente en `tools/optimizar_malla.py` (agrupación espacial de vértices) sin reemplazarlo. Se agregó `tools/suavizar_obj.py` para suavizado Laplaciano conservador de OBJ triangulares, con protección de vértices en bordes y aristas no manifold, parámetros acotados, protección contra sobrescritura e informe JSON. Pruebas unitarias nuevas en `tests/test_suavizar_obj.py`.

```bash
python -m tools.suavizar_obj modelo_reparado.obj --salida modelo_suavizado.obj --iteraciones 2 --intensidad 0.25
```

**Pendiente:** ejecutar pruebas CI y verificar con mallas reales. La reducción de polígonos existente opera sobre STL; no se ha conectado todavía un simplificador OBJ. El suavizado puede alterar detalles y dimensiones; no se certifica aptitud para impresión.
