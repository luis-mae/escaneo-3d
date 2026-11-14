# Arquitectura objetivo — ESCANEO 3D

## Estado de la implementación

La rama principal conserva el prototipo de procesamiento local. La interfaz PWA puede instalarse en navegadores compatibles; el service worker cachea exclusivamente recursos estáticos y nunca cachea rutas API. La captura desde cámara móvil se incorpora a la selección de fotografías. El servidor local sigue siendo de confianza y no debe exponerse a Internet.

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

El endpoint local actual no implementa autenticación ni aislamiento multiusuario. No reutilizarlo como API pública.

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