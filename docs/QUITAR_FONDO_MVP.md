# Herramienta «Quitar fondo» en ESCANEO 3D

La interfaz web incluye un proceso independiente: seleccionar una fotografía,
pulsar «Quitar fondo», revisar la vista previa y descargar un PNG transparente.

## Dependencia opcional en el servidor

```bash
python -m pip install "rembg[cpu]"
```

El primer uso puede descargar pesos del modelo y demorar. El procesamiento
se realiza en el servidor, no en el navegador móvil. Las fotos se transmiten
al servidor configurado pero esta ruta no las guarda como proyectos.
El resultado se devuelve directamente al dispositivo.

**Límites:** JPG/PNG de hasta 10 MB y 16 megapíxeles; un procesamiento
simultáneo por servidor. Sin rembg instalado, la API responde 503 con
instrucciones. La herramienta no sustituye la reconstrucción fotogramétrica:
las fotos sin fondo son una salida opcional y no se usan automáticamente
en COLMAP. La precisión del recorte depende de la fotografía.
