# Registro de decisiones

- Nombre de producto: Escaneo3D. Nombre de repositorio solicitado: `escaneo`.
- Alcance inicial: objetos pequeños y piezas mecánicas; uso potencial para impresión 3D.
- Plataformas objetivo: Android, iOS, PWA.
- Captura guiada y automática; plantilla de escala opcional.
- FREE local, PLUS local con más cuota, PRO híbrido/externo.
- Cuotas tentativas: 5/25/50 trabajos por mes; precios no definidos.
- Formatos básicos: STL, OBJ, PLY, GLB, 3MF; CAD avanzado STEP/IGES/DXF sujeto a ingeniería inversa real.
- Pendiente de validar: motores, viabilidad de procesamiento local, arquitectura final, precios y políticas de tiendas.

- UX acordada: la acción principal al terminar un modelo será **«Guardar o exportar a…»**. Al seleccionarla, el usuario elige el formato/destino (impresión 3D, malla/intercambio, nube de puntos, visualización o CAD), con explicación de compatibilidad, escala y limitaciones. No mostrar una lista técnica de descargas como flujo principal.
- Plan vigente de producto: diez etapas en `docs/ROADMAP_10_ETAPAS.md`; no publicar hasta completar criterios y obtener autorización expresa.

- 14/11/2026: el flujo principal de salida se denomina «Guardar o exportar a…». La interfaz permite elegir STL, OBJ y PLY; GLB, 3MF y CAD quedan visibles como próximos hasta incorporar conversores reales.
- 14/11/2026: la interfaz web avanza como PWA instalable con caché de recursos estáticos, captura desde cámara móvil y biblioteca local de proyectos. La caché no incluye rutas API ni archivos del usuario.
- 14/11/2026: no se expondrá el servidor FastAPI actual a Internet; carece de autenticación y aislamiento multiusuario. La arquitectura remota se documenta por separado y exige identidad, almacenamiento privado, cola persistente y controles de costos.
