# Etapa 116 — Reparación conservadora de mallas

Se agregó `tools/reparar_malla.py` para leer OBJ triangulares, descartar caras degeneradas y duplicadas, orientar caras vecinas y cerrar únicamente agujeros triangulares aislados. Se genera un informe de aristas abiertas, aristas no manifold y conflictos de orientación; no se sobreescriben resultados. Se añadieron pruebas unitarias.

```bash
python -m tools.reparar_malla modelo.obj --salida modelo_reparado.obj
```

**Alcance:** reparación geométrica limitada y experimental; no rellena agujeros grandes, no garantiza orientación global ni certifica impresión 3D. Las pruebas no fueron ejecutadas todavía.
