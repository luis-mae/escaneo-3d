# Avance 82 — Fusión automática de nubes prealineadas

Se integran `correspondencias_3d` y `fusion_robusta` en `tools/fusion_prealineada.py`, con correspondencias recíprocas generadas automáticamente entre cada nube y la base, ajuste Sim(3) robusto y exportación PLY/JSON.

Uso: `python -m tools.fusion_prealineada entrada.json --salida resultados --radio 0.1 --umbral 0.02 --voxel 0.01`. Entrada: `{"nubes": [[[x,y,z],...], [[x,y,z],...]]}`.

Se agregan cuatro pruebas sintéticas de integración. **No ejecutadas en CI aún.** Requiere `numpy`, `scipy` y las dependencias del módulo PLY existente.

**Restricción esencial:** las nubes deben estar ya aproximadamente alineadas en el mismo marco y escala; no es SfM global ni un registro inicial robusto a grandes desplazamientos, y no demuestra precisión métrica.
