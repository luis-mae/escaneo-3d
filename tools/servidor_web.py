"""API local para recibir fotos y lanzar COLMAP en segundo plano.

Requiere FastAPI, python-multipart y uvicorn; COLMAP debe estar instalado.
Pensada para ejecución local/confiable, NO para exponer directamente a Internet.
"""
import os
import re
import shutil
import threading
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from tools.pipeline_colmap import pipeline_colmap
from tools.colmap_a_malla import nube_colmap_a_malla
from tools.exportar_formatos_3d import exportar_formatos

RAIZ = Path(os.environ.get("ESCANEO3D_DATA", "datos_escaneo")).resolve()
WEB = Path(__file__).resolve().parents[1] / "web"
MAX_ARCHIVOS = 100
MAX_BYTES = 20 * 1024 * 1024
MAX_TOTAL = 500 * 1024 * 1024
ESTADOS = {}
CERROJO = threading.Lock()
app = FastAPI(title="ESCANEO 3D API", version="0.122")


def _actualizar(identificador, **cambios):
    with CERROJO:
        ESTADOS[identificador].update(cambios)


def _procesar(identificador, carpeta):
    _actualizar(identificador, estado="procesando")
    try:
        informe = pipeline_colmap(carpeta / "fotos", carpeta / "resultado")
        _actualizar(identificador, estado="completado",
                    resultado=informe["disperso"]["estado"])
    except Exception as exc:
        _actualizar(identificador, estado="error",
                    error=f"{type(exc).__name__}: {str(exc)[:400]}")


@app.post("/api/proyectos", status_code=202)
async def crear_proyecto(nombre: str = Form(...), fotos: list[UploadFile] = File(...)):
    nombre = nombre.strip()
    if not 1 <= len(nombre) <= 80:
        raise HTTPException(400, "Nombre de proyecto inválido")
    if not 3 <= len(fotos) <= MAX_ARCHIVOS:
        raise HTTPException(400, "Se requieren entre 3 y 100 fotos")
    tipos = {"image/jpeg": ".jpg", "image/png": ".png"}
    if any(f.content_type not in tipos for f in fotos):
        raise HTTPException(400, "COLMAP admite JPG o PNG; convertí WebP antes de enviar")
    identificador = uuid.uuid4().hex
    carpeta = RAIZ / identificador
    destino = carpeta / "fotos"
    destino.mkdir(parents=True, exist_ok=False)
    total = 0
    try:
        for indice, foto in enumerate(fotos):
            extension = tipos[foto.content_type]
            ruta = destino / f"imagen_{indice:04d}{extension}"
            with ruta.open("xb") as salida:
                cantidad = 0
                while True:
                    bloque = await foto.read(1024 * 1024)
                    if not bloque:
                        break
                    cantidad += len(bloque)
                    total += len(bloque)
                    if cantidad > MAX_BYTES or total > MAX_TOTAL:
                        raise HTTPException(413, "Tamaño de carga excedido")
                    salida.write(bloque)
                if cantidad == 0:
                    raise HTTPException(400, "Imagen vacía")
        with CERROJO:
            ESTADOS[identificador] = {"id": identificador, "nombre": nombre,
                                     "fotos": len(fotos), "estado": "en_cola"}
        threading.Thread(target=_procesar, args=(identificador, carpeta),
                         daemon=True).start()
        return ESTADOS[identificador].copy()
    except Exception:
        shutil.rmtree(carpeta, ignore_errors=True)
        raise
    finally:
        for foto in fotos:
            await foto.close()


@app.get("/api/proyectos/{identificador}")
def estado_proyecto(identificador: str):
    with CERROJO:
        if identificador not in ESTADOS:
            raise HTTPException(404, "Proyecto no encontrado")
        return ESTADOS[identificador].copy()


@app.get("/api/proyectos/{identificador}/nube")
def descargar_nube(identificador: str):
    with CERROJO:
        estado = ESTADOS.get(identificador)
    if not estado or estado["estado"] != "completado":
        raise HTTPException(404, "Nube no disponible")
    archivos = sorted((RAIZ / identificador / "resultado").glob("modelo_*.ply"))
    if not archivos:
        raise HTTPException(404, "Nube no disponible")
    return FileResponse(archivos[0], filename="escaneo3d_nube.ply",
                        media_type="application/octet-stream")



@app.post("/api/proyectos/{identificador}/malla", status_code=202)
def generar_malla(identificador: str, alpha: float = 0.05):
    """Construye OBJ experimental desde la nube COLMAP."""
    import math
    if not math.isfinite(alpha) or not 0 < alpha <= 1000:
        raise HTTPException(400, "Alpha inválido")
    with CERROJO:
        registro = ESTADOS.get(identificador)
        if not registro or registro["estado"] != "completado":
            raise HTTPException(409, "Reconstrucción no completada")
        if registro.get("malla") in ("procesando", "completada"):
            raise HTTPException(409, "Malla ya iniciada")
        registro["malla"] = "procesando"
    carpeta = RAIZ / identificador / "resultado"
    nubes = sorted(carpeta.glob("modelo_*.ply"))
    if not nubes:
        _actualizar(identificador, malla="error", error_malla="Nube PLY ausente")
        raise HTTPException(404, "Nube PLY ausente")

    def ejecutar():
        try:
            nube_colmap_a_malla(nubes[0], carpeta / "malla.obj", alpha)
            _actualizar(identificador, malla="completada")
        except Exception as exc:
            _actualizar(identificador, malla="error",
                        error_malla=f"{type(exc).__name__}: {str(exc)[:300]}")
    threading.Thread(target=ejecutar, daemon=True).start()
    return {"id": identificador, "malla": "procesando"}


@app.get("/api/proyectos/{identificador}/malla")
def descargar_malla(identificador: str):
    with CERROJO:
        registro = ESTADOS.get(identificador)
        disponible = registro and registro.get("malla") == "completada"
    ruta = RAIZ / identificador / "resultado" / "malla.obj"
    if not disponible or not ruta.is_file():
        raise HTTPException(404, "Malla OBJ no disponible")
    return FileResponse(ruta, filename="escaneo3d_malla.obj",
                        media_type="application/octet-stream")



@app.post("/api/proyectos/{identificador}/exportaciones", status_code=202)
def preparar_exportaciones(identificador: str):
    """Exporta OBJ, PLY y STL; unidades físicas no verificadas."""
    with CERROJO:
        registro = ESTADOS.get(identificador)
        if not registro or registro.get("malla") != "completada":
            raise HTTPException(409, "Primero generá la malla OBJ")
        if registro.get("exportaciones") in ("procesando", "completadas"):
            raise HTTPException(409, "Exportaciones ya iniciadas")
        registro["exportaciones"] = "procesando"
    carpeta = RAIZ / identificador / "resultado"
    def ejecutar():
        try:
            exportar_formatos(carpeta / "malla.obj", carpeta / "exportaciones")
            _actualizar(identificador, exportaciones="completadas")
        except Exception as exc:
            _actualizar(identificador, exportaciones="error",
                        error_exportaciones=f"{type(exc).__name__}: {str(exc)[:300]}")
    threading.Thread(target=ejecutar, daemon=True).start()
    return {"id": identificador, "exportaciones": "procesando"}


@app.get("/api/proyectos/{identificador}/exportaciones/{formato}")
def descargar_exportacion(identificador: str, formato: str):
    if formato not in ("obj", "ply", "stl"):
        raise HTTPException(400, "Formato no admitido")
    with CERROJO:
        registro = ESTADOS.get(identificador)
        disponible = registro and registro.get("exportaciones") == "completadas"
    ruta = RAIZ / identificador / "resultado" / "exportaciones" / ("modelo." + formato)
    if not disponible or not ruta.is_file():
        raise HTTPException(404, "Exportación no disponible")
    return FileResponse(ruta, filename="escaneo3d_modelo." + formato,
                        media_type="application/octet-stream")


app.mount("/", StaticFiles(directory=str(WEB), html=True), name="web")
