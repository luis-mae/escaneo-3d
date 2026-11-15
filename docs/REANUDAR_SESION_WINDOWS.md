# Recuperar la sesión real de COLMAP en Windows

**Objetivo:** aprovechar los archivos PLY ya calculados, sin repetir la extracción de características ni el emparejamiento de las 41 fotos.

Desde la carpeta del repositorio, abrir una consola con Python y las dependencias instaladas. Ejecutar:

```bat
reanudar_escaneo_windows.bat "A:\escaneo3d" "A:\escaneo3d_resultado"
```

La primera ruta debe apuntar a la carpeta donde están los resultados de COLMAP, o a una carpeta superior que los contenga. La segunda debe ser una **carpeta nueva**, fuera de la primera. Si los resultados están en otra ubicación, reemplazar la primera ruta. **No borrar ni mover los archivos anteriores.**

El lanzador primero lista las nubes disponibles, después intenta mallar la más apropiada y finalmente exporta OBJ, STL y GLB a `A:\escaneo3d_resultado\modelo_3d\exportados`. Si falla, conservar los informes `ERROR_MALLA.txt`, `ERROR.txt` y los archivos intermedios; no repetir COLMAP automáticamente.

También se puede usar Python directamente:

```bat
python -m tools.verificar_sesion_mvp "A:\escaneo3d"
python -m tools.escanear_fotos_mvp "A:\escaneo3d" --reanudar --salida "A:\escaneo3d_resultado"
```

**Limitación esencial:** la reconstrucción dispersa de COLMAP produce puntos 3D, pero no necesariamente una superficie fiel. Una envolvente convexa puede perder concavidades y detalles; exportar un STL no certifica que sea imprimible. Es necesario abrir el GLB/OBJ, comprobar la forma y validar escala y topología. El resultado de estas órdenes todavía no se ha comprobado con la sesión real del usuario.
