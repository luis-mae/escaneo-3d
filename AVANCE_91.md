# Avance 91 — Verificación estructural de exportaciones

Se incorporó `tools/verificar_exportacion.py`, que comprueba presencia y coherencia de PLY e informe JSON, cantidad de vértices, filas válidas, coordenadas finitas y hashes SHA-256 de los dos archivos. Se agregan cinco pruebas sintéticas.

Uso: `python -m tools.verificar_exportacion resultados/`.

Esta verificación detecta truncamientos y discrepancias de estructura, pero no demuestra integridad histórica sin hashes de referencia externos, ni exactitud dimensional o funcionamiento fotogramétrico de extremo a extremo. Pruebas CI aún no confirmadas.
