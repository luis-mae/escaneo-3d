# Avance 90 — Protección de exportaciones

La CLI de fusión controlada prepara primero PLY y JSON en un directorio temporal y solo después los mueve a los destinos finales. Se rechaza sobrescribir archivos existentes salvo que se indique explícitamente `--sobrescribir`. Se agregan pruebas de no sobrescritura y entradas inválidas.

**Limitación:** el reemplazo de los dos archivos no constituye una transacción atómica conjunta ante interrupciones entre ambos movimientos. La ejecución de CI y la validación con fotografías reales permanecen pendientes.
