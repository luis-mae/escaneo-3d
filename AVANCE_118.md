# Etapa 118 — Exportación de modelos OBJ, PLY y STL

Se implementó `tools/exportar_formatos_3d.py` para exportar mallas triangulares OBJ a tres formatos: OBJ, PLY ASCII con caras triangulares y STL binario. Cada exportación se guarda en una carpeta nueva, junto con informe JSON, tamaños y hashes SHA256; no se sobrescriben resultados. Se agregaron pruebas unitarias que incluyen lectura del STL mediante el verificador existente.

```bash
python -m tools.exportar_formatos_3d modelo_suavizado.obj --salida exportaciones_modelo
```

**Estado:** código guardado en GitHub, sin pruebas reales ejecutadas. Las unidades no están certificadas y una exportación STL no garantiza que el modelo sea imprimible. **Siguiente etapa: 119, interfaz para carga de fotografías.**
