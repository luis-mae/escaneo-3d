# Arquitectura objetivo — ESCANEO 3D

## Estado de la implementación

La rama principal conserva el prototipo de procesamiento local. La interfaz PWA puede instalarse en navegadores compatibles; el service worker cachea exclusivamente recursos estáticos y nunca cachea rutas API. La captura desde cámara móvil se incorpora a la selección de fotografías. El servidor local sigue siendo de confianza y no debe exponerse a Internet. Se incorporó una base opcional de autenticación JWT HS256, aislamiento de proyectos por subject y cuotas transaccionales; todavía no reemplaza la arquitectura pública objetivo.

## Etapa 7 — Backend remoto PRO

### Arquitectura objetivo
- API pública detrás de HTTPS, gateway y protección antiabuso.
- Servicio de identidad separado del motor de reconstrucción.
- Almacenamiento privado por usuario/proyecto con URLs firmadas de corta duración.
- Cola persistente (por ejemplo Redis + workers) para separar peticiones HTTP de trabajos COLMAP.
- Workers en contenedores aislados, límites de CPU/RAM/GPU, timeout y cancelación.
- Estado persistente: queued, preprocessing, sparse, dense, meshing, exporting, completed, failed, cancelled.
- Retención configurable, borrado verificable y política de backups.
- Instrumentación: latencia por fase, éxito/fallo, consumo CPU/GPU, almacenamiento y costo por trabajo; no registrar fotografías ni datos sensibles en logs.

### Contrato mínimo de servicios
- POST /v1/projects crea proyecto y devuelve ID.
- POST /v1/projects/{id}/uploads crea cargas firmadas.
- POST /v1/projects/{id}/jobs inicia reconstrucción con perfil y límites.
- GET /v1/jobs/{id} consulta estado y métricas no sensibles.
- POST /v1/jobs/{id}/cancel solicita cancelación.
- GET /v1/projects/{id}/artifacts enumera exportaciones disponibles.
- DELETE /v1/projects/{id} inicia borrado de datos y artefactos.

El endpoint local puede activar autenticación JWT HS256 y aislamiento por propietario mediante `ESCANEO3D_AUTH_REQUIRED=1`; requiere un emisor externo y una PWA que gestione tokens. El endpoint de cuenta consulta entitlements y permite eliminación de cuenta/proyectos. Aún carece de gateway, OIDC completo, almacenamiento privado remoto, cola distribuida, aislamiento de workers y rate limiting. No reutilizarlo como API pública.

## Etapa 8 — Cuentas, planes y pagos

### Modelo de dominio
- User: identidad externa, correo verificado, preferencias y estado.
- Subscription: plan, proveedor, identificador externo, periodo y estado.
- Entitlement: cuota efectiva y capacidades habilitadas.
- UsageEvent: trabajo consumido, unidades, fecha y referencia idempotente.
- PaymentEvent: evento de proveedor verificado; nunca confiar en el retorno del navegador.
- Refund/Cancellation: estado y trazabilidad.

### Reglas obligatorias
- Verificar firma de webhooks en backend y procesar eventos idempotentemente.
- No almacenar datos de tarjetas; tokenización por proveedor de pagos.
- Aplicar cuota en servidor antes de encolar un trabajo.
- Reservar cuota al iniciar y liquidar al finalizar; liberar si falla antes de consumir.
- Reembolsos, cancelaciones y renovaciones sincronizados con el proveedor.
- Precios, impuestos, moneda y disponibilidad por país configurables.
- FREE local no requiere pago ni envío de fotos a infraestructura remota.
- No habilitar cobros hasta elegir proveedor, jurisdicciones, condiciones legales y costos reales.

## Etapa 9 — Experiencia y navegación

Navegación prevista: Inicio/Nuevo escaneo; Capturar fotografías; Procesamiento y progreso; Visor y calidad; Guardar o exportar a; Mis modelos; Cuenta y plan (cuando exista identidad). La experiencia debe usar lenguaje comprensible: la persona elige el resultado que necesita, no nombres de algoritmos. Las advertencias técnicas aparecen cuando cambian una decisión (escala, malla abierta, formato no disponible).

## Etapa 10 — Seguridad y publicación

- HTTPS, autenticación, autorización por proyecto y aislamiento entre usuarios.
- Validación de tipo real, tamaño, resolución, nombres, rutas y contenido de archivos.
- Límites de concurrencia, cuotas, rate limiting y protección de costos.
- Auditoría de dependencias/licencias y SBOM.
- Política de privacidad, consentimiento, exportación y borrado de datos.
- Pruebas de recuperación, concurrencia, dispositivos, accesibilidad y rendimiento.
- Beta privada, soporte, telemetría mínima y proceso de incidentes.
- Publicación escalonada solo tras aprobación expresa.

## Dependencias externas que no se deben simular

El backend remoto requiere elegir infraestructura y presupuesto. Cuentas y pagos requieren seleccionar proveedor y completar sus verificaciones comerciales. Publicación móvil requiere cuentas de desarrollador y firma de aplicaciones. Mientras no estén disponibles esos elementos, se desarrolla la integración desacoplada y se mantiene desactivada la operación comercial.

## Motor de cuotas implementado
`tools/entitlements.py` incorpora una base SQLite con cuentas de plan, periodo mensual UTC, reservas idempotentes de trabajos y liquidación como consumido o liberado. La API vincula el subject JWT con proyectos y cuotas, consulta el plan y aplica reservas antes de encolar. Las cuotas FREE 5, PLUS 25 y PRO 50 son parámetros iniciales de referencia, no precios ni compromisos comerciales. No procesa pagos ni sincroniza suscripciones con un proveedor.


### Configuración Docker autenticada (base, no despliegue público)
- Copiar `.env.example` a `.env`; mantener `ESCANEO3D_AUTH_REQUIRED=0` para uso local.
- Para pruebas de integración remota, activar `ESCANEO3D_AUTH_REQUIRED=1`, configurar secreto HS256 aleatorio (mínimo 32 bytes), issuer y audience.
- La base SQLite de cuotas se persiste en el volumen `/data/entitlements.sqlite3`.
- El archivo `.env` se excluye de Git y del contexto de construcción Docker.
- No exponer el puerto de Compose públicamente: el binding local actual usa `127.0.0.1`; cualquier acceso externo exige HTTPS, gateway y controles aún pendientes.


## Exportación empaquetada
La exportación permite seleccionar formatos, crear opcionalmente un ZIP con los archivos elegidos y descargar un manifiesto con tamaños y SHA-256. La regeneración se realiza en una carpeta temporal y sustituye la exportación anterior solo después de preparar la nueva correctamente.
