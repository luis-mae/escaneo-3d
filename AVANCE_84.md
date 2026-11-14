# Avance 84 — Pruebas automáticas reproducibles

Se incorporan dependencias Python declaradas y un flujo de GitHub Actions que instala las dependencias y ejecuta `python -m unittest discover -s tests -v` en cada push y pull request, además de permitir ejecución manual.

**Estado:** archivos de automatización incorporados; la aprobación de pruebas solo se puede confirmar una vez que GitHub Actions termine satisfactoriamente. La ejecución sintética no sustituye pruebas con fotografías reales, dispositivos móviles ni control dimensional.
