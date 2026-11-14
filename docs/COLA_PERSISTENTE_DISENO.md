# Etapa 7 — Cola persistente (módulo aislado)

Se agregó `tools/cola_persistente.py`, una base SQLite transaccional para encolar identificadores de trabajo sin almacenar fotos ni credenciales. Incluye alta idempotente, reclamo atómico, lease renovable, finalización condicionada al worker y cancelación de trabajos pendientes por propietario.

**Estado:** módulo implementado y pruebas escritas; **no está conectado** al servidor web ni al pipeline COLMAP. No representa procesamiento remoto listo para producción.

## Integración futura
1. Integrar la cola con el ciclo de vida actual y las reservas de cuotas, sin doble consumo.
2. Implementar worker separado que valide propietario, permisos, ubicación de archivos y recursos.
3. Agregar heartbeat y recuperación de leases vencidos; cuando se agoten los intentos, marcar fallo definitivo y liberar cuota.
4. Incorporar aislamiento de procesos, límites de CPU/RAM/GPU y logs redactados.
5. Sustituir SQLite por backend compartido apropiado antes de escalar a varios nodos, o garantizar un único host y almacenamiento consistente.
6. Probar apagados abruptos, concurrencia, cancelación, reintentos, idempotencia y recuperación.

**Advertencia:** leases vencidos no detienen procesos antiguos. Antes de ejecutar trabajos reales, se requiere un mecanismo de fencing o exclusión para evitar doble procesamiento y escrituras simultáneas. No exponer a Internet ni publicar todavía.
