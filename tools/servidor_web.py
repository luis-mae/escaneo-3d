"""API local para recibir fotos y lanzar COLMAP en segundo plano.

Requiere FastAPI, python-multipart y uvicorn; COLMAP debe estar instalado.
Pensada para ejecución local/confiable, NO para exponer directamente a Internet.
"""
import os
import json
import re
import shutil
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, UnidentifiedImageError

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
MAX_PIXELES = 100_000_000
ESTADOS = {}
CERROJO = threading.Lock()
app = FastAPI(title="ESCANEO 3D API", version="0.125")



def _validar_imagen(ruta, formato_esperado):
    """Comprueba el contenido real de la imagen, no solo el MIME declarado."""
    try:
        with Image.open(ruta) as imagen:
            if imagen.format != formato_esperado:
                raise ValueError("El contenido no coincide con el tipo declarado")
            ancho, alto = imagen.size
            if ancho <= 0 or alto <= 0 or ancho * alto > MAX_PIXELES:
                raise ValueError("Resolución de imagen no admitida")
            imagen.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("Archivo de imagen inválido o dañado") from exc


def _guardar_estado(identificador):
    carpeta = RAIZ / identificador
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / "estado.json"
    temporal = carpeta / ("estado." + uuid.uuid4().hex + ".tmp")
    try:
        temporal.write_text(json.dumps(ESTADOS[identificador], ensure_ascii=False), encoding="utf-8")
        os.replace(temporal, destino)
    finally:
        temporal.unlink(missing_ok=True)


def _recuperar_estados():
    if not RAIZ.exists():
        return
    for archivo in RAIZ.glob("*/estado.json"):
        if not re.fullmatch(r"[a-f0-9]{32}", archivo.parent.name):
            continue
        try:
            registro = json.loads(archivo.read_text(encoding="utf-8"))
            if registro.get("id") != archivo.parent.name:
                continue
            registro.setdefault("creado_en", datetime.fromtimestamp(
                archivo.parent.stat().st_ctime, timezone.utc).isoformat())
            if registro.get("estado") in ("en_cola", "procesando"):
                registro["estado"] = "interrumpido"
            for clave in ("malla", "exportaciones"):
                if registro.get(clave) == "procesando":
                    registro[clave] = "interrumpido"
            ESTADOS[registro["id"]] = registro
            _guardar_estado(registro["id"])
        except (OSError, ValueError, TypeError):
            continue


def _actualizar(identificador, **cambios):
    with CERROJO:
        ESTADOS[identificador].update(cambios)
        _guardar_estado(identificador)


def _procesar(identificador, carpeta):
    _actualizar(identificador, estado="procesando")
    try:
        informe = pipeline_colmap(
            carpeta / "fotos", carpeta / "resultado",
            denso=bool(ESTADOS[identificador].get("solicitar_denso", False)),
        )
        resultado = carpeta / "resultado"
        nube_densa = resultado / "dense_0" / "fused.ply"
        nubes_dispersas = sorted(resultado.glob("modelo_*.ply"))
        if not nube_densa.is_file() and not nubes_dispersas:
            raise RuntimeError("COLMAP no produjo una nube PLY utilizable")
        _actualizar(
            identificador, estado="completado",
            resultado=informe["disperso"]["estado"],
            reconstruccion_densa=("completada" if nube_densa.is_file()
                                  else ("fallida" if informe.get("error_denso")
                                        else "no_solicitada")),
            archivo_nube=("dense_0/fused.ply" if nube_densa.is_file()
                          else nubes_dispersas[0].name),
        )
    except Exception as exc:
        _actualizar(identificador, estado="error",
                    error=f"{type(exc).__name__}: {str(exc)[:400]}")


@app.post("/api/proyectos", status_code=202)
async def crear_proyecto(nombre: str = Form(...), solicitar_denso: bool = Form(False),
                         fotos: list[UploadFile] = File(...)):
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
            formato = "JPEG" if extension == ".jpg" else "PNG"
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
            try:
                _validar_imagen(ruta, formato)
            except ValueError as exc:
                raise HTTPException(400, str(exc)) from exc
        with CERROJO:
            ESTADOS[identificador] = {"id": identificador, "nombre": nombre,
                                     "fotos": len(fotos), "estado": "en_cola",
                                     "creado_en": datetime.now(timezone.utc).isoformat(),
                                     "solicitar_denso": solicitar_denso,
                                     "reconstruccion_densa": ("pendiente" if solicitar_denso else "no_solicitada")}
        with CERROJO:
            _guardar_estado(identificador)
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
    resultado = RAIZ / identificador / "resultado"
    archivo_denso = resultado / "dense_0" / "fused.ply"
    archivos = sorted(resultado.glob("modelo_*.ply"))
    archivo = archivo_denso if archivo_denso.is_file() else (archivos[0] if archivos else None)
    if archivo is None:
        raise HTTPException(404, "Nube no disponible")
    return FileResponse(archivo, filename="escaneo3d_nube.ply",
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
        _guardar_estado(identificador)
    carpeta = RAIZ / identificador / "resultado"
    nube_densa = carpeta / "dense_0" / "fused.ply"
    nubes = [nube_densa] if nube_densa.is_file() else sorted(carpeta.glob("modelo_*.ply"))
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
        _guardar_estado(identificador)
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



@app.delete("/api/proyectos/{identificador}")
def eliminar_proyecto(identificador: str):
    """Elimina fotos y resultados cuando no existen trabajos activos."""
    if not re.fullmatch(r"[a-f0-9]{32}", identificador):
        raise HTTPException(404, "Proyecto no encontrado")
    with CERROJO:
        registro = ESTADOS.get(identificador)
        if registro is None:
            raise HTTPException(404, "Proyecto no encontrado")
        if registro.get("estado") in ("en_cola", "procesando"):
            raise HTTPException(409, "Reconstrucción en curso")
        if any(registro.get(k) == "procesando" for k in ("malla", "exportaciones")):
            raise HTTPException(409, "Procesamiento en curso")
        try:
            shutil.rmtree(RAIZ / identificador)
        except OSError as exc:
            raise HTTPException(500, "No se pudo eliminar el proyecto") from exc
        del ESTADOS[identificador]
    return {"id": identificador, "eliminado": True}


@app.get("/api/proyectos")
def listar_proyectos():
    with CERROJO:
        proyectos = [registro.copy() for registro in ESTADOS.values()]
        proyectos.sort(key=lambda p: p.get("creado_en", ""), reverse=False)
        return {"proyectos": proyectos}


_recuperar_estados()
app.mount("/", StaticFiles(directory=str(WEB), html=True), name="web")
