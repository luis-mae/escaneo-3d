# Avance 86 — Control de aceptación de registro

Se añade `tools/registro_con_control.py`: ejecuta ICP, consulta cobertura bidireccional y devuelve un indicador explícito de aprobación experimental. También se valida el mínimo de correspondencias de ICP y se distingue un resultado de cobertura insuficiente. Se agregan cuatro casos de prueba entre los archivos nuevos y modificados.

Uso: `python -m tools.registro_con_control entrada.json --salida resultado.json --radio 0.05 --cobertura-minima 0.6`.

Pendiente ejecutar pruebas en CI y validar con escaneos reales. La aceptación geométrica no certifica exactitud métrica.
