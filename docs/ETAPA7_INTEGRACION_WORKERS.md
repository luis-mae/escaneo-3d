# Integración pendiente: workers y pipeline real

La cola SQLite y el worker base siguen **aislados del servidor web**. No se debe confundir la existencia de estos módulos con un backend remoto funcional.

## Protocolo mínimo
- `reclamar_con_token(worker)` obtiene (id, token) en una sola transacción; evita consultar después un token que podría haber cambiado.
- Renovación y finalización exigen token vigente, worker coincidente y lease no vencido.
- El callback del worker es experimental: no debe escribir archivos finales ni cobrar cuotas hasta que exista fencing en el almacenamiento y reconciliación de entitlements.
- El trabajo que excede su lease puede seguir ejecutándose; el token bloquea su finalización en la cola, **no** impide escrituras externas.
- `agotar_vencidos` y `fallidos_por_agotamiento` son herramientas de conciliación; aún falta integrar la liberación de cuotas y evitar repetirla.
- Los tests agregados son unitarios y no reemplazan pruebas de COLMAP, hardware ni despliegue.

## Siguientes implementaciones
1. Almacenar cada ejecución en carpeta temporal por token de lease; promover resultados únicamente bajo control transaccional del propietario del trabajo.
2. Agregar mecanismo de cancelación del proceso y límite de recursos con aislamiento.
3. Integrar estados del servidor, cuotas y cola en una operación idempotente.
4. Persistir auditoría sin fotografías ni datos identificables y métricas de costo real.
5. Probar fallos, apagados abruptos y cargas concurrentes antes de cualquier servicio público.
