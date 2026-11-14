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
MAX_PIXELES_PROYECTO = 500_000_000
MAX_TRABAJOS_EN_COLA = 3
SEM_TRABAJOS = threading.Semaphore(1)
ESTADOS = {}
CERROJO = threading.Lock()
app = FastAPI(title="ESCANEO 3D API", version="0.125")



def _estimar_alpha_puntos(puntos):
    """Sugiere alpha según el espaciamiento local; es una heurística, no escala física."""
    import numpy as np
    from scipy.spatial import cKDTree

    nube = np.asarray(puntos, dtype=float)
    if nube.ndim != 2 or nube.shape[1] != 3 or len(nube) < 4 or not np.isfinite(nube).all():
        raise ValueError("No hay suficientes puntos válidos para estimar alpha")
    if len(nube) > 50_000:
        indices = np.linspace(0, len(nube) - 1, 50_000, dtype=int)
        muestra = nube[indices]
    else:
        muestra = nube
    distancias, _ = cKDTree(muestra).query(muestra, k=2)
    cercania = distancias[:, 1]
    cercania = cercania[np.isfinite(cercania) & (cercania > 0)]
    if not len(cercania):
        raise ValueError("No se pudo estimar el espaciamiento de la nube")
    return float(np.median(cercania) * 3.0)


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
            return ancho * alto
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
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
            if registro.get("malla") == "procesando":
                registro["malla"] = "interrumpido"
                resultado = archivo.parent / "resultado"
                (resultado / "malla.obj").unlink(missing_ok=True)
                (resultado / "malla.informe.json").unlink(missing_ok=True)
            if registro.get("exportaciones") == "procesando":
                registro["exportaciones"] = "interrumpido"
                shutil.rmtree(archivo.parent / "resultado" / "exportaciones",
                              ignore_errors=True)
            ESTADOS[registro["id"]] = registro
            _guardar_estado(registro["id"])
        except (OSError, ValueError, TypeError):
            continue


def _actualizar(identificador, **cambios):
    with CERROJO:
        ESTADOS[identificador].update(cambios)
        _guardar_estado(identificador)


def _procesar_impl(identificador, carpeta):
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
            error_reconstruccion_densa=informe.get("error_denso"),
            archivo_nube=("dense_0/fused.ply" if nube_densa.is_file()
                          else nubes_dispersas[0].name),
        )
    except Exception as exc:
        solicitar_denso = bool(ESTADOS.get(identificador, {}).get("solicitar_denso"))
        _actualizar(identificador, estado="error",
                    reconstruccion_densa=("error" if solicitar_denso else "no_solicitada"),
                    error=f"{type(exc).__name__}: {str(exc)[:400]}")


def _procesar(identificador, carpeta):
    """Serializa trabajos intensivos para proteger CPU y memoria del servidor."""
    with SEM_TRABAJOS:
        _procesar_impl(identificador, carpeta)


def _ejecutar_con_semaforo(funcion):
    with SEM_TRABAJOS:
        funcion()


@app.get("/api/salud")
def salud():
    """Diagnóstico mínimo sin revelar rutas ni configuración sensible."""
    with CERROJO:
        activos = sum(
            r.get("estado") in ("en_cola", "procesando")
            or r.get("malla") == "procesando"
            or r.get("exportaciones") == "procesando"
            for r in ESTADOS.values()
        )
    colmap = shutil.which("colmap") is not None
    return {
        "estado": "listo" if colmap else "motor_no_detectado",
        "colmap_detectado": colmap,
        "reconstruccion_densa": "disponible_sujeta_a_GPU_y_recursos" if colmap else "no_disponible",
        "trabajos_en_cola": activos,
        "limite_trabajos": MAX_TRABAJOS_EN_COLA,
    }


@app.post("/api/proyectos", status_code=202)
async def crear_proyecto(nombre: str = Form(...), fotos: list[UploadFile] = File(...),
                         solicitar_denso: bool = Form(False)):
    nombre = nombre.strip()
    if not 1 <= len(nombre) <= 80:
        raise HTTPException(400, "Nombre de proyecto inválido")
    if not 3 <= len(fotos) <= MAX_ARCHIVOS:
        raise HTTPException(400, "Se requieren entre 3 y 100 fotos")
    with CERROJO:
        ocupados = sum(
            r.get("estado") in ("en_cola", "procesando")
            or r.get("malla") == "procesando"
            or r.get("exportaciones") == "procesando"
            for r in ESTADOS.values()
        )
        if ocupados >= MAX_TRABAJOS_EN_COLA:
            raise HTTPException(429, "Servidor ocupado; esperá a que termine otro trabajo")
    tipos = {"image/jpeg": ".jpg", "image/png": ".png"}
    if any(f.content_type not in tipos for f in fotos):
        raise HTTPException(400, "COLMAP admite JPG o PNG; convertí WebP antes de enviar")
    identificador = uuid.uuid4().hex
    carpeta = RAIZ / identificador
    destino = carpeta / "fotos"
    destino.mkdir(parents=True, exist_ok=False)
    total = 0
    total_pixeles = 0
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
                pixeles = _validar_imagen(ruta, formato)
                total_pixeles += pixeles
                if total_pixeles > MAX_PIXELES_PROYECTO:
                    raise ValueError("La resolución total del proyecto excede el límite")
            except ValueError as exc:
                raise HTTPException(400, str(exc)) from exc
        with CERROJO:
            ocupados = sum(
                r.get("estado") in ("en_cola", "procesando")
                or r.get("malla") == "procesando"
                or r.get("exportaciones") == "procesando"
                for r in ESTADOS.values()
            )
            if ocupados >= MAX_TRABAJOS_EN_COLA:
                raise HTTPException(429, "Servidor ocupado; esperá a que termine otro trabajo")
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
def generar_malla(identificador: str, alpha: float | None = None):
    """Construye OBJ experimental desde la nube COLMAP."""
    import math
    if alpha is not None and (not math.isfinite(alpha) or not 0 < alpha <= 1000):
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
            alpha_usado = alpha
            if alpha_usado is None:
                from tools.leer_colmap_ply import leer_nube_colmap_ply
                puntos = leer_nube_colmap_ply(nubes[0], max_puntos=50_000, submuestrear=True)
                alpha_usado = _estimar_alpha_puntos(puntos)
            informe_malla = nube_colmap_a_malla(
                nubes[0], carpeta / "malla.obj", alpha_usado,
                max_puntos=50_000, submuestrear=True
            )
            _actualizar(identificador, malla="completada",
                        alpha_malla=alpha_usado,
                        informe_malla=informe_malla)
        except Exception as exc:
            (carpeta / "malla.obj").unlink(missing_ok=True)
            (carpeta / "malla.informe.json").unlink(missing_ok=True)
            _actualizar(identificador, malla="error",
                        error_malla=f"{type(exc).__name__}: {str(exc)[:300]}")
    threading.Thread(target=_ejecutar_con_semaforo,
                     args=(ejecutar,), daemon=True).start()
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
            shutil.rmtree(carpeta / "exportaciones", ignore_errors=True)
            _actualizar(identificador, exportaciones="error",
                        error_exportaciones=f"{type(exc).__name__}: {str(exc)[:300]}")
    threading.Thread(target=_ejecutar_con_semaforo,
                     args=(ejecutar,), daemon=True).start()
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
