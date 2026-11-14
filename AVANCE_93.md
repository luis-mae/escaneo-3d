# Avance 93 — Manifiesto de integridad SHA-256

El exportador de fusión controlada genera `manifiesto_sha256.json` con las huellas criptográficas del PLY y del informe JSON. El verificador compara las huellas si encuentra el manifiesto. Se incorporan pruebas de integración y de detección de modificaciones. El modo sin sobrescritura también protege el manifiesto.

**Límites:** el manifiesto no está firmado y puede reemplazarse junto con los archivos. Los tres movimientos de archivo no son atómicos como conjunto. CI y escaneos reales aún pendientes de verificación.
