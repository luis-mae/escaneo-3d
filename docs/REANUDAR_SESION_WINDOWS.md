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

## Alternativa de mayor fidelidad: nube densa (solo equipo con CUDA)

Si la malla generada desde puntos dispersos se ve deformada, no seguir ajustando
alpha indefinidamente: la nube sparse carece de información de superficie.
En un equipo **con GPU NVIDIA compatible y COLMAP compilado con CUDA**, se puede
reutilizar el modelo sparse ya calculado y producir una nube densa:

```bat
python -m tools.colmap_denso_mvp --fotos "A:\escaneo3d\images" --sparse "A:\escaneo3d\sparse\0" --salida "A:\escaneo3d_denso" --gpu
```

Las rutas son ejemplos: localizar la carpeta real de fotos y los archivos
`cameras.bin`, `images.bin` y `points3D.bin`. El proceso puede consumir
muchos recursos y tiempo. **No ejecutar este comando en un equipo sin CUDA**.
El script conserva el modelo sparse, escribe `informe_denso.json` y, si
termina, `fused.ply`. Después se puede ejecutar el lanzador de recuperación
sobre `A:\escaneo3d_denso` con una carpeta de salida nueva.

En una PC sin GPU CUDA, el flujo disponible continúa siendo la nube dispersa
y su malla aproximada: no se debe presentar como escaneo fiel.
