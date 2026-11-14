# Avance 81 — Correspondencias 3D recíprocas

Se agrega `tools/correspondencias_3d.py` para generar pares de puntos automáticamente **solo cuando las nubes ya están prealineadas**. Usa KD-trees, distancia máxima explícita y correspondencia mutua uno a uno. Rechaza entradas inválidas y menos de tres pares.

Ejemplo: `python -m tools.correspondencias_3d entrada.json --salida pares.json --radio 0.05`.

Entrada: `{"origen": [[x,y,z],...], "destino": [[x,y,z],...]}`. El resultado incluye pares, índices, distancias y advertencias. Para usarlo con `fusion_robusta.fusionar`, pasar `{"origen": ..., "destino": ...}` en el orden correspondiente al marco de cada nube; revisar la convención de origen/destino antes de integrar.

**Limitaciones:** no estima una alineación inicial, no identifica puntos físicos homólogos en fotografías, no recupera escala métrica y no demuestra precisión dimensional. El resultado necesita validación con escaneos reales. Se agregan cinco pruebas unitarias, todavía sin ejecución confirmada en CI.
