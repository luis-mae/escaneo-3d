# Avance 83 — Auditoría bidireccional del registro

Se agrega `tools/auditar_registro.py` para evaluar la cobertura de nubes registradas mediante distancias de vecino más próximo en ambas direcciones, RMSE y percentil 95. La transformación de entrada debe ser una similitud válida (escala positiva, rotación ortonormal, traslación finita).

Uso: `python -m tools.auditar_registro entrada.json --salida auditoria.json --umbral 0.05 --cobertura-minima 0.6`.

Entrada JSON: `origen`, `destino` (nubes Nx3) y `transformacion` con `escala`, `rotacion` y `traslacion`. Se agregan seis pruebas unitarias. La ejecución integral en CI y la validación con escaneos reales siguen pendientes.

**Limitaciones:** una cobertura alta puede ocurrir en geometrías repetitivas o incorrectas; no certifica registro correcto, escala física, exactitud dimensional ni aptitud para impresión.
