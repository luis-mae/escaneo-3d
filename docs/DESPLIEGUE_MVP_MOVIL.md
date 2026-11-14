# ESCANEO 3D — Despliegue remoto del MVP (en preparación)

Este documento es una guía de implementación, **no** certifica que exista un MVP publicado.

## Estado comprobable

La PWA, la API FastAPI, el contenedor Docker, el adaptador COLMAP y los exportadores ya existen. El backend usa archivos JSON por proyecto y memoria de proceso para estados activos; al reiniciar marca trabajos activos como interrumpidos. **No es una cola distribuida**. La validación con fotografías reales sigue pendiente.

## Despliegue privado, no público todavía

El archivo `docker-compose.production.yml` es una base de despliegue **privado**. Exige las tres variables JWT y mantiene el puerto enlazado exclusivamente a `127.0.0.1`. El gateway HTTPS, proveedor de identidad, sesión PWA, protección antiabuso y validación de infraestructura aún no están integrados. No cambiar el puerto a `0.0.0.0` ni abrirlo al público.

El secreto JWT debe ser aleatorio y tener al menos 32 bytes. El proveedor que emita JWT HS256 debe compartir ese secreto de forma segura, establecer `iss`, `aud`, `sub`, `exp` y respetar el máximo de 24 horas. No colocar secretos en GitHub ni en el frontend.

Comprobar configuración (sin iniciar el servicio):

```sh
docker compose -f docker-compose.production.yml config --quiet
```

Iniciar únicamente en una máquina privada con recursos suficientes:

```sh
docker compose -f docker-compose.production.yml up --build -d
```

El límite de 8 GiB RAM y 4 CPU es **un presupuesto inicial a ajustar con mediciones reales**, no un dimensionamiento validado. COLMAP denso puede requerir GPU y no está garantizado en este contenedor CPU. Los proyectos se guardan en un volumen Docker persistente, que **no equivale a un backup**.

## Bloqueos para publicar desde un celular

1. Implementar proveedor de identidad y sesión PWA; el backend actual valida JWT, pero la interfaz aún no realiza el login.
2. Asegurar aislamiento y control de trabajos concurrentes en la infraestructura elegida; por ahora operar con una sola réplica.
3. Agregar reverse proxy HTTPS, controles de tamaño/rate limiting y políticas de privacidad/retención.
4. Confirmar costos, credenciales y permisos del alojamiento **antes** de contratarlo.
5. Realizar prueba real: cámara móvil → subida → COLMAP → malla → visor → STL/OBJ/GLB.
6. Comprobar recuperación tras cierre del navegador, reinicio del servidor y fallos de reconstrucción.

**Criterio MVP:** un usuario real completa la reconstrucción de un objeto desde el teléfono y descarga una malla 3D, con evidencias del resultado. No confundir una demo estática o tests con esta validación.
