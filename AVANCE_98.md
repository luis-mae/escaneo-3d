# Avance 98 — Reprocesamiento controlado de PLY

La interfaz `tools.fusion_desde_ply` incorpora `--sobrescribir`, compatible con el exportador verificado y su manifiesto SHA-256. Sin la opción, conserva las exportaciones existentes; con la opción, permite regenerarlas. Se añade prueba de integración que comprueba rechazo de sobrescritura implícita y regeneración explícita.

El porcentaje de etapas no equivale al porcentaje de una aplicación terminada. Sigue pendiente verificar la ejecución de pruebas y la reconstrucción con fotografías reales.
