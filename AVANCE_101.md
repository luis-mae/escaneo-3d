# Etapa 101 — Primer flujo integrado fotos → PLY → OBJ opcional

Se añadió `tools/fotos_a_modelo.py`, que integra reconstrucción experimental de dos vistas, exportación de nube PLY, informe JSON y superficie alpha-shape OBJ opcional. Rechaza reconstrucciones insuficientes, parámetros inválidos y sobrescritura no autorizada. Prepara archivos antes de moverlos al destino.

Ejemplo:

```bash
python -m tools.fotos_a_modelo foto01.jpg foto02.jpg --focal-px 1200 --salida resultados
python -m tools.fotos_a_modelo foto01.jpg foto02.jpg --focal-px 1200 --salida resultados --alpha 0.5 --sobrescribir
```

La focal en píxeles debe conocerse o estimarse adecuadamente para la resolución utilizada. El resultado conserva **escala arbitraria**; la malla alpha-shape es opcional, experimental y no garantiza volumen cerrado, medidas correctas ni aptitud de impresión. El método aún procesa solo dos fotos y **no implementa SfM multivista completo**.

Se incorporaron pruebas con simulación controlada de la salida del motor, que **no sustituyen** fotografías reales. Pendiente ejecutar CI y pruebas reales.
