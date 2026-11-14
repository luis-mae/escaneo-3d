# Avance 100 — Prueba integral reproducible del flujo PLY

Se añadió `tests/test_flujo_completo_ply.py`, con pruebas sintéticas de importación PLY, registro rígido local, fusión voxelizada, exportación, manifiesto SHA-256 y verificación de consistencia. También verifica que nubes sin solapamiento no produzcan archivos de salida.

Para ejecutar localmente: `python -m pip install -r requirements.txt` y `python -m unittest discover -s tests -v`.

**Estado:** 100 hitos de implementación registrados, pero NO significa producto 100 % funcional. La ejecución de CI no ha podido confirmarse; aún faltan pruebas con fotografías reales, reconstrucción fotogramétrica integral, evaluación de precisión y puesta a punto de la experiencia de usuario.
