# ESCANEO 3D — Plan de cierre del MVP (15/11/2026)

**Objetivo único:** fotografías reales → reconstrucción reconocible → visualización → exportación OBJ/GLB/STL, con limitaciones explícitas. No equivale a CAD dimensional.

## Orden obligatorio (no confundir commits con avance)
1. **Reproducir y medir:** recuperar la sesión real A:\\escaneo3d; inspeccionar fotografías, modelos sparse, nubes PLY y registros; identificar si hay nube densa o solo dispersa. No repetir COLMAP si los datos ya existen.
2. **Obtener geometría reconocible:** si existe nube densa, usarla como primera opción; si solo hay nube dispersa, no presentar la envolvente convexa como escaneo fiel. Determinar si hace falta densificación externa con CUDA o cambiar método; registrar decisión.
3. **Validar exportación:** abrir el resultado en visor independiente y verificar que OBJ, STL y GLB representan la misma geometría. Documentar errores y escala.
4. **Integrar el circuito en la PWA:** fotos → trabajo → progreso/errores → vista → guardar/exportar. Solo corregir defectos bloqueantes.
5. **Prueba de aceptación:** una pieza real reconocible con fotos originales, registro de ejecución y exportación abierta; idealmente segunda pieza con concavidad para documentar límites.

## Evidencia requerida para declarar MVP
- Carpeta de fotografías reales identificada, con cantidad de tomas.
- Logs de procesamiento real y ruta de nube/malla resultante.
- Captura de pantalla del modelo que permita compararlo con el objeto.
- Archivos exportados que se abran en software independiente.
- Registro de limitaciones de forma, escala, tiempo y hardware.

## Regla de honestidad
Código implementado ≠ prueba superada ≠ MVP validado. Sin archivos reales disponibles no se puede verificar la fidelidad geométrica. No inventar porcentajes ni afirmar éxito por CI.

## Priorización
80% reconstrucción real; 15% integración indispensable; 5% correcciones bloqueantes. Posponer comercio, cuentas, UI cosmética, formatos adicionales y otras funciones.

## Próximo punto de decisión
Con la sesión real de COLMAP, revisar si hay `fused.ply` o una nube comparablemente densa. Si solo existen ~7.600 puntos dispersos, una malla generada por alpha-shape puede ser geométricamente inválida aunque exporte sin errores. No gastar más tiempo puliendo exportadores antes de resolverlo.
