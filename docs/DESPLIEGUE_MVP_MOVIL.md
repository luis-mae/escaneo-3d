# ESCANEO 3D — Despliegue remoto del MVP (en preparación)

Este documento es una guía de implementación, **no** certifica que exista un MVP publicado.

## Estado comprobable

La PWA, la API FastAPI, el contenedor Docker, el adaptador COLMAP y los exportadores ya existen. El backend usa archivos JSON por proyecto y memoria de proceso para estados activos; al reiniciar marca trabajos activos como interrumpidos. **No es una cola distribuida**. La validación con fotografías reales sigue pendiente.

## Despliegue privado detrás de HTTPS

El servidor ya incorpora login privado con contraseña PBKDF2, JWT temporal de una hora, límites de solicitudes, aislamiento de proyectos por usuario y recuperación de trabajos interrumpidos. El frontend incluye el formulario de acceso y descarga autenticada. **No hay aún un servidor desplegado ni una prueba real de reconstrucción certificada.**

Requisitos: servidor Linux con Docker Compose, 4 CPU y al menos 8 GiB de RAM para la primera prueba (a validar), almacenamiento persistente y un dominio apuntando al servidor. Instalar Caddy en el host y adaptar `deploy/Caddyfile.example`. Mantener una sola réplica de la API y **no exponer el puerto 8000 a Internet**.

En el servidor, dentro del repositorio:

```sh
cp .env.production.example .env.production
chmod 600 .env.production
# Editar los valores de .env.production y generar el secreto JWT.
# Para la contraseña, ejecutar el comando de generación incluido en el ejemplo.
# El hash contiene caracteres $: colocarlo entre comillas simples en el archivo .env.production.
docker compose --env-file .env.production -f docker-compose.production.yml config --quiet
docker compose --env-file .env.production -f docker-compose.production.yml up --build -d
docker compose --env-file .env.production -f docker-compose.production.yml ps
curl -fsS http://127.0.0.1:8000/api/salud
```

El login inicial utiliza el usuario configurado en `ESCANEO3D_MVP_USER`. Al arrancar se crea su cuenta FREE si no existe; no se reactiva ninguna cuenta deshabilitada. Para esta beta privada hay una cuota inicial de cinco reconstrucciones por mes. El sistema no implementa cobros.

**Importante:** `docker compose` no carga automáticamente el archivo llamado `.env.production`; siempre pasar `--env-file .env.production`. No subirlo a GitHub. Mantener copia de seguridad del volumen persistente. El contenedor está limitado a 8 GiB RAM y 4 CPU, sin garantía de rendimiento COLMAP hasta medirlo con fotos reales. La reconstrucción densa puede requerir GPU.

## Bloqueos para publicar desde un celular

1. Disponer de servidor, dominio y HTTPS válidos para abrir la aplicación desde el celular.
2. Comprobar capacidad real de CPU/RAM/disco, tiempos de COLMAP y mantener una sola réplica.
3. Configurar Caddy HTTPS, revisar límites y definir privacidad, backups y retención de fotografías.
4. Confirmar costos, credenciales y permisos del alojamiento **antes** de contratarlo.
5. Realizar prueba real: cámara móvil → subida → COLMAP → malla → visor → STL/OBJ/GLB.
6. Comprobar recuperación tras cierre del navegador, reinicio del servidor y fallos de reconstrucción.

**Criterio MVP:** un usuario real completa la reconstrucción de un objeto desde el teléfono y descarga una malla 3D, con evidencias del resultado. No confundir una demo estática o tests con esta validación.
