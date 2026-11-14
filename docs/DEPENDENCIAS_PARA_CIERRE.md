# Dependencias para completar ESCANEO 3D

Este documento separa trabajo de software de acciones que requieren recursos, cuentas o evidencia física. Ninguna de estas dependencias se marca como completada por tener un diseño o una interfaz.

## Evidencia técnica y validación
- Fotografías originales de objetos reales, incluyendo pieza prismática, pieza con agujeros/concavidades y objeto orgánico mate.
- Dimensiones físicas de referencia medidas con instrumento adecuado.
- Equipo objetivo para medir tiempos, memoria y GPU; COLMAP real no se certifica con fixtures.
- Validación de malla y exportaciones en programas externos (slicer, CAD y visor GLB cuando se incorpore).

## Backend PRO
- Elegir proveedor de cómputo con CPU/GPU y presupuesto operativo.
- Elegir almacenamiento privado y región de datos.
- Aprovisionar base de datos, cola persistente y observabilidad.
- Configurar dominio, DNS, TLS, secretos y política de backup/retención.
- Definir límites de costos y procedimiento de incidentes antes de habilitar usuarios.

## Identidad, planes y pagos
- Elegir proveedor de identidad o método de autenticación.
- Confirmar países de operación, moneda, impuestos y condiciones de servicio.
- Elegir procesador de pagos y completar alta comercial/verificación.
- Definir precios, cuotas y reglas de reembolso usando costos reales de procesamiento.
- Configurar webhooks firmados y credenciales de producción; no incluir secretos en Git.

## Publicación móvil
- Decidir si se distribuye inicialmente como PWA o si se prepara Android/iOS nativo.
- Para tiendas: cuentas de desarrollador, certificados, firma, capturas, textos legales y revisión.
- Probar en dispositivos físicos de distintas capacidades y sistemas operativos.

## Condición de publicación
No publicar ni activar cobros hasta que las etapas técnicas, la validación física, la privacidad, los costos y los controles de seguridad estén verificados. La publicación requiere autorización expresa.
