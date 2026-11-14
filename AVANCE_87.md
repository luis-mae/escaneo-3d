# Avance 87 — Fusión con control de calidad

Se añadió `tools/fusion_con_control.py`: registra nubes prealineadas contra una base fija mediante ICP rígido, exige cobertura bidireccional mínima y aborta la fusión si alguna nube no pasa el control. Puede agrupar por vóxeles y exporta PLY e informe JSON.

Uso: `python -m tools.fusion_con_control entrada.json --salida resultados --radio 0.1 --cobertura-minima 0.6 --voxel 0.01`.

Cinco pruebas sintéticas agregadas. Pendiente ejecutar CI y validar con escaneos reales. No resuelve escala desconocida, prealineación ni fotogrametría desde fotografías.
