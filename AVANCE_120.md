# Etapa 120 — Interfaz conectada a COLMAP

Se agregó `tools/servidor_web.py`: servidor FastAPI local que recibe fotografías JPG/PNG, valida cantidades y límites de tamaño, guarda los archivos en una carpeta de trabajo independiente, lanza `pipeline_colmap` en un hilo y ofrece consulta de estado y descarga de nube PLY. `web/app.js` permite enviar fotos y consultar el progreso. Se añadieron `requirements-web.txt`.

Para ejecutar en equipo con COLMAP instalado:

```bash
pip install -r requirements-web.txt
python -m uvicorn tools.servidor_web:app --host 127.0.0.1 --port 8000
```

Abrir http://127.0.0.1:8000/ . **No exponer este servidor directamente a Internet:** todavía carece de autenticación, cuotas por usuario, cola persistente, cancelación, limpieza de datos y endurecimiento de seguridad. El estado se pierde al reiniciar el servidor. Se requiere COLMAP nativo en PATH; la salida actual es nube dispersa PLY, no malla STL. No se han ejecutado pruebas reales de extremo a extremo ni se ha publicado.
