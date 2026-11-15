"""API local para recibir fotos y lanzar COLMAP en segundo plano.

Requiere FastAPI, python-multipart y uvicorn; COLMAP debe estar instalado.
Pensada para ejecución local/confiable, NO para exponer directamente a Internet.
"""
import os
import json
import hashlib
import re
import shutil
import threading
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from tools.pipeline_colmap import pipeline_colmap
from tools.consulta_worker import consultar_trabajo
from tools.colmap_a_malla import nube_colmap_a_malla
from tools.reparar_malla import reparar_obj
from tools.exportar_formatos_3d import exportar_formatos
from tools.calidad_fotografias import analizar_carpeta
from tools.auth import TokenInvalido, validar_token
from tools.limites_api import permitir
from tools.login_mvp import comprobar_clave, emitir_token
from tools.entitlements import obtener_entitlements, reservar_trabajo, finalizar_trabajo, eliminar_cuenta

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
CANCELACIONES = {}
CERROJO = threading.Lock()
app = FastAPI(title="ESCANEO 3D API", version="0.126")

# Fail closed when explicitly running in production; never expose a public
# deployment with local-mode authentication accidentally disabled.
MODO_PRODUCCION = os.environ.get("ESCANEO3D_ENV", "local").strip().lower() == "production"
if MODO_PRODUCCION:
    if os.environ.get("ESCANEO3D_AUTH_REQUIRED", "").strip().lower() not in ("1", "true", "yes"):
        raise RuntimeError("Producción requiere ESCANEO3D_AUTH_REQUIRED=1")
    if len(os.environ.get("ESCANEO3D_JWT_SECRET", "").encode("utf-8")) < 32:
        raise RuntimeError("Producción requiere ESCANEO3D_JWT_SECRET de al menos 32 bytes")
    if not os.environ.get("ESCANEO3D_JWT_ISSUER", "").strip():
        raise RuntimeError("Producción requiere ESCANEO3D_JWT_ISSUER")
    if not os.environ.get("ESCANEO3D_JWT_AUDIENCE", "").strip():
        raise RuntimeError("Producción requiere ESCANEO3D_JWT_AUDIENCE")
    if not os.environ.get("ESCANEO3D_MVP_USER", "").strip():
        raise RuntimeError("Producción requiere ESCANEO3D_MVP_USER")
    hash_clave = os.environ.get("ESCANEO3D_MVP_PASSWORD_HASH", "")
    try:
        algoritmo, iteraciones, sal, digest = hash_clave.split("$")
        hash_valido = (algoritmo == "pbkdf2_sha256" and int(iteraciones) >= 600000
                       and len(bytes.fromhex(sal)) >= 16
                       and len(bytes.fromhex(digest)) == 32)
    except (ValueError, TypeError):
        hash_valido = False
    if not hash_valido:
        raise RuntimeError("Producción requiere hash PBKDF2 válido de contraseña")




@app.middleware("http")
async def cabeceras_y_rutas_seguras(request: Request, call_next):
    """Endurece respuestas y bloquea IDs manipulados antes de resolver rutas."""
    ruta = request.url.path
    if MODO_PRODUCCION:
        ip = request.client.host if request.client else "desconocido"
        permitido, espera = permitir(ip, ruta, request.method)
        if not permitido:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                {"detail": "Demasiadas solicitudes; reintentá más tarde"},
                status_code=429, headers={"Retry-After": str(espera), "Cache-Control": "no-store"}
            )
    if ruta.startswith("/api/proyectos/"):
        segmentos = ruta.split("/")
        if len(segmentos) > 3 and not re.fullmatch(r"[a-f0-9]{32}", segmentos[3]):
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Proyecto no encontrado"}, status_code=404)
    auth_requerida = os.environ.get("ESCANEO3D_AUTH_REQUIRED", "").lower() in ("1", "true", "yes")
    if auth_requerida and ruta.startswith("/api/") and ruta not in ("/api/salud", "/api/sesion"):
        try:
            usuario = validar_token(request.headers.get("authorization"))
        except RuntimeError:
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Autenticación remota mal configurada"}, status_code=503)
        except TokenInvalido as exc:
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": str(exc)}, status_code=401)
        request.state.user_id = usuario
        segmentos = ruta.split("/")
        if len(segmentos) > 3 and segmentos[2] == "proyectos":
            identificador = segmentos[3]
            with CERROJO:
                proyecto = ESTADOS.get(identificador)
                propietario = proyecto.get("user_id") if proyecto else None
            if propietario != usuario:
                from fastapi.responses import JSONResponse
                return JSONResponse({"detail": "Proyecto no encontrado"}, status_code=404)
    respuesta = await call_next(request)
    respuesta.headers["X-Content-Type-Options"] = "nosniff"
    respuesta.headers["Referrer-Policy"] = "no-referrer"
    respuesta.headers["X-Frame-Options"] = "DENY"
    respuesta.headers["Permissions-Policy"] = "camera=(self), microphone=(), geolocation=()"
    respuesta.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "img-src 'self' data: blob:; connect-src 'self'; "
        "worker-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    )
    if ruta.startswith("/api/"):
        respuesta.headers["Cache-Control"] = "no-store, max-age=0"
        respuesta.headers["Pragma"] = "no-cache"
    return respuesta



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


def _estado_publico(registro):
    """Evita exponer identificadores internos de identidad en respuestas API."""
    salida = registro.copy()
    salida.pop("user_id", None)
    salida.pop("usage_event_id", None)
    return salida


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
                propietario = registro.get("user_id")
                if propietario:
                    try:
                        finalizar_trabajo(propietario, registro.get("usage_event_id") or registro["id"], exito=False)
                    except (ValueError, KeyError, OSError):
                        pass
                registro["estado"] = "interrumpido"
                registro["error"] = (
                    "El servidor se reinició durante la reconstrucción. "
                    "Las fotos originales siguen guardadas; elegí Reintentar "
                    "para iniciar nuevamente COLMAP sin volver a subirlas."
                )
                registro["interrumpido_en"] = datetime.now(timezone.utc).isoformat()
            if registro.get("malla") == "procesando":
                resultado = archivo.parent / "resultado"
                # Conservar una malla completa si el servidor se reinició justo
                # después de escribirla, antes de persistir el estado.
                completa = ((resultado / "malla.obj").is_file() and
                            (resultado / "malla.obj").stat().st_size > 0 and
                            (resultado / "malla.informe.json").is_file())
                registro["malla"] = "completada" if completa else "interrumpido"
                if not completa:
                    (resultado / "malla.obj").unlink(missing_ok=True)
                    (resultado / "malla.informe.json").unlink(missing_ok=True)
            if registro.get("malla") == "completada":
                resultado = archivo.parent / "resultado"
                if not (resultado / "malla.obj").is_file() or (resultado / "malla.obj").stat().st_size == 0:
                    registro["malla"] = "interrumpido"
                    registro["error_malla"] = "La malla OBJ guardada no está disponible; regenerala"
            if registro.get("exportaciones") == "completadas":
                resultado = archivo.parent / "resultado" / "exportaciones"
                if not (resultado / "informe_exportacion.json").is_file():
                    registro["exportaciones"] = "interrumpido"
                    registro["error_exportaciones"] = "Faltan los archivos exportados; volvé a prepararlos"
            if registro.get("exportaciones") == "procesando":
                resultado = archivo.parent / "resultado"
                # No destruir exportaciones completas por un reinicio del servidor.
                # Una carpeta instalada se conserva y se puede descargar nuevamente.
                registro["exportaciones"] = ("completadas" if
                    (resultado / "exportaciones" / "informe_exportacion.json").is_file()
                    else "interrumpido")
                for temporal in resultado.glob("exportaciones_tmp_*"):
                    if temporal.is_dir():
                        shutil.rmtree(temporal, ignore_errors=True)
            ESTADOS[registro["id"]] = registro
            _guardar_estado(registro["id"])
        except (OSError, ValueError, TypeError):
            continue


def _actualizar(identificador, **cambios):
    with CERROJO:
        ESTADOS[identificador].update(cambios)
        _guardar_estado(identificador)


def _procesar_impl(identificador, carpeta, cancel_event=None):
    try:
        _actualizar(identificador, estado="procesando")
        if cancel_event is not None and cancel_event.is_set():
            from tools.proceso_controlado import ProcesoCancelado
            raise ProcesoCancelado("Trabajo cancelado antes de iniciar COLMAP")
        opciones_pipeline = {
            "denso": bool(ESTADOS[identificador].get("solicitar_denso", False))
        }
        if cancel_event is not None:
            opciones_pipeline["cancel_event"] = cancel_event
        informe = pipeline_colmap(
            carpeta / "fotos", carpeta / "resultado", **opciones_pipeline
        )
        if cancel_event is not None and cancel_event.is_set():
            from tools.proceso_controlado import ProcesoCancelado
            raise ProcesoCancelado("Trabajo cancelado al finalizar COLMAP")
        resultado = carpeta / "resultado"
        modelo_denso = str(informe.get("modelo_denso_elegido", "0"))
        nube_densa = resultado / ("dense_" + modelo_denso) / "fused.ply"
        nubes_dispersas = sorted(resultado.glob("modelo_*.ply"))
        # Una fusión interrumpida puede dejar un fused.ply parcial: no utilizarlo.
        if (informe.get("error_denso") or not informe.get("denso")
                or informe["denso"].get("estado") != "completado"):
            nube_densa = resultado / "__denso_no_completado__.ply"
        elif nube_densa.is_file() and nube_densa.stat().st_size == 0:
            nube_densa.unlink()
        nubes_dispersas = [archivo for archivo in nubes_dispersas
                            if _nube_utilizable(archivo)]
        from tools.motor_colmap import _cantidad_vertices_ply
        nubes_dispersas.sort(key=_cantidad_vertices_ply, reverse=True)
        if nube_densa.is_file() and not _nube_utilizable(nube_densa):
            nube_densa = resultado / "__denso_no_completado__.ply"
        if not nube_densa.is_file() and not nubes_dispersas:
            raise RuntimeError("COLMAP no produjo una nube PLY con al menos cuatro puntos; "
                               "revisá el solapamiento, nitidez y textura de las fotografías")
        if ESTADOS[identificador].get("user_id"):
            finalizar_trabajo(ESTADOS[identificador]["user_id"], ESTADOS[identificador].get("usage_event_id") or identificador, exito=True)
        _actualizar(
            identificador, estado="completado",
            resultado=informe["disperso"]["estado"],
            reconstruccion_densa=("completada" if nube_densa.is_file()
                                  else ("fallida" if opciones_pipeline["denso"]
                                        else "no_solicitada")),
            error_reconstruccion_densa=(informe.get("error_denso") or
                                        ("La nube densa no se generó correctamente"
                                         if opciones_pipeline["denso"] and not nube_densa.is_file()
                                         else None)),
            archivo_nube=(f"dense_{modelo_denso}/fused.ply" if nube_densa.is_file()
                          else nubes_dispersas[0].name),
        )
        # El MVP no depende de que el navegador permanezca abierto: iniciar
        # la generación de OBJ automáticamente después de COLMAP.
        try:
            generar_malla(identificador)
        except Exception as exc:
            _actualizar(identificador, malla="error",
                        error_malla=f"No se pudo iniciar el mallado automático: {str(exc)[:220]}")
    except Exception as exc:
        propietario = ESTADOS.get(identificador, {}).get("user_id")
        if propietario:
            try:
                finalizar_trabajo(propietario, ESTADOS.get(identificador, {}).get("usage_event_id") or identificador, exito=False)
            except ValueError:
                pass
        solicitar_denso = bool(ESTADOS.get(identificador, {}).get("solicitar_denso"))
        cancelado = cancel_event is not None and cancel_event.is_set()
        _actualizar(
            identificador,
            estado=("cancelado" if cancelado else "error"),
            reconstruccion_densa=("cancelada" if cancelado and solicitar_denso
                                  else ("error" if solicitar_denso else "no_solicitada")),
            error=("Trabajo cancelado por solicitud del usuario" if cancelado
                   else f"{type(exc).__name__}: {str(exc)[:400]}"),
            cancelacion_solicitada=False,
        )


def _procesar(identificador, carpeta, cancel_event=None):
    """Serializa trabajos intensivos para proteger CPU y memoria del servidor."""
    try:
        with SEM_TRABAJOS:
            _procesar_impl(identificador, carpeta, cancel_event)
    finally:
        with CERROJO:
            CANCELACIONES.pop(identificador, None)


def _ejecutar_con_semaforo(funcion):
    with SEM_TRABAJOS:
        funcion()


@app.post("/api/sesion")
async def iniciar_sesion(request: Request):
    """Acceso privado para el primer MVP, solo sobre HTTPS público."""
    if not MODO_PRODUCCION:
        raise HTTPException(404, "No disponible en modo local")
    if not os.environ.get("ESCANEO3D_MVP_PASSWORD_HASH"):
        raise HTTPException(503, "Acceso privado no configurado")
    try:
        datos = await request.json()
    except ValueError:
        raise HTTPException(400, "JSON inválido")
    if not isinstance(datos, dict):
        raise HTTPException(400, "Datos inválidos")
    usuario = datos.get("usuario")
    clave = datos.get("clave")
    configurado = os.environ.get("ESCANEO3D_MVP_USER", "")
    if not isinstance(usuario, str) or not isinstance(clave, str) or len(clave) > 1024:
        raise HTTPException(400, "Credenciales inválidas")
    import hmac
    # Ejecutar PBKDF2 incluso para usuarios incorrectos: reduce filtración
    # de la existencia del usuario por diferencias de tiempo de respuesta.
    clave_correcta = comprobar_clave(clave)
    usuario_correcto = bool(configurado) and hmac.compare_digest(usuario, configurado)
    if not (usuario_correcto and clave_correcta):
        raise HTTPException(401, "Usuario o contraseña incorrectos")
    return {"token": emitir_token(configurado), "tipo": "Bearer", "expira_en": 3600}


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
        "formatos_exportacion": ["obj", "ply", "stl", "glb", "3mf", "nube"],
        "version_api": "0.126",
        "modo": "remoto_autenticado" if MODO_PRODUCCION else "local_no_exponer_a_internet",
    }


@app.post("/api/proyectos", status_code=202)
async def crear_proyecto(request: Request, nombre: str = Form(...), fotos: list[UploadFile] = File(...),
                         solicitar_denso: bool = Form(False)):
    nombre = nombre.strip()
    if not 1 <= len(nombre) <= 80:
        raise HTTPException(400, "Nombre de proyecto inválido")
    if not 3 <= len(fotos) <= MAX_ARCHIVOS:
        raise HTTPException(400, "Se requieren entre 3 y 100 fotos")
    if shutil.which("colmap") is None:
        raise HTTPException(503, "El motor COLMAP no está instalado o no está disponible en PATH; instalalo antes de cargar fotos")
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
    usuario = getattr(request.state, "user_id", None)
    reserva = False
    evento_uso = uuid.uuid4().hex if usuario else None
    if usuario:
        try:
            permisos = obtener_entitlements(usuario)
            if solicitar_denso and not permisos["capacidades"]["reconstruccion_densa_remota"]:
                raise PermissionError("La reconstrucción densa remota requiere plan PRO activo")
            reservar_trabajo(usuario, evento_uso)
            reserva = True
        except (KeyError, PermissionError, ValueError) as exc:
            raise HTTPException(403, str(exc)) from exc
    carpeta = RAIZ / identificador
    destino = carpeta / "fotos"
    total = 0
    total_pixeles = 0
    try:
        destino.mkdir(parents=True, exist_ok=False)
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
        # Preflight de captura: detecta problemas de imagen antes de consumir COLMAP.
        # Es una heurística orientativa; nunca descarta automáticamente las fotos.
        try:
            informe_captura = analizar_carpeta(destino)
            (carpeta / "informe_captura.json").write_text(
                json.dumps(informe_captura, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            resumen_captura = {
                "cantidad": informe_captura["cantidad"],
                "aptas_preliminares": sum(
                    x.get("estado") == "apta_preliminar" for x in informe_captura["imagenes"]
                ),
                "revisar": sum(
                    x.get("estado") == "revisar" for x in informe_captura["imagenes"]
                ),
                "no_decodificables": sum(
                    x.get("estado") == "no_decodificable" for x in informe_captura["imagenes"]
                ),
            }
        except Exception as exc:
            informe_captura = None
            resumen_captura = {"error": f"{type(exc).__name__}: {str(exc)[:180]}"}
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
                                     "user_id": usuario, "usage_event_id": evento_uso, "fotos": len(fotos), "estado": "en_cola",
                                     "creado_en": datetime.now(timezone.utc).isoformat(),
                                     "solicitar_denso": solicitar_denso,
                                     "reconstruccion_densa": ("pendiente" if solicitar_denso else "no_solicitada"),
                                     "calidad_captura": resumen_captura}
        with CERROJO:
            _guardar_estado(identificador)
        evento_cancelacion = threading.Event()
        with CERROJO:
            CANCELACIONES[identificador] = evento_cancelacion
        try:
            threading.Thread(target=_procesar,
                             args=(identificador, carpeta, evento_cancelacion),
                             daemon=True).start()
        except Exception:
            with CERROJO:
                CANCELACIONES.pop(identificador, None)
                ESTADOS.pop(identificador, None)
            raise
        return _estado_publico(ESTADOS[identificador])
    except Exception:
        shutil.rmtree(carpeta, ignore_errors=True)
        if reserva:
            try:
                finalizar_trabajo(usuario, evento_uso, exito=False)
            except ValueError:
                pass
        raise
    finally:
        for foto in fotos:
            await foto.close()


@app.post("/api/proyectos/{identificador}/cancelar", status_code=202)
def cancelar_proyecto(identificador: str):
    """Solicita cancelación de una reconstrucción COLMAP en cola o en ejecución."""
    with CERROJO:
        registro = ESTADOS.get(identificador)
        if not registro:
            raise HTTPException(404, "Proyecto no encontrado")
        if registro.get("estado") not in ("en_cola", "procesando"):
            raise HTTPException(409, "El proyecto no tiene una reconstrucción cancelable")
        evento = CANCELACIONES.get(identificador)
        if evento is None:
            raise HTTPException(409, "El trabajo no tiene un proceso activo que pueda cancelarse")
        evento.set()
        registro["cancelacion_solicitada"] = True
        _guardar_estado(identificador)
    return {"id": identificador, "estado": "cancelacion_solicitada"}


@app.post("/api/proyectos/{identificador}/reintentar", status_code=202)
def reintentar_proyecto(identificador: str):
    """Reinicia una reconstrucción fallida/cancelada usando las fotos ya guardadas."""
    with CERROJO:
        registro = ESTADOS.get(identificador)
        if not registro:
            raise HTTPException(404, "Proyecto no encontrado")
        if registro.get("estado") not in ("error", "cancelado", "interrumpido"):
            raise HTTPException(409, "Solo se pueden reintentar trabajos fallidos, cancelados o interrumpidos")
        if registro.get("malla") == "procesando" or registro.get("exportaciones") == "procesando":
            raise HTTPException(409, "Hay otra operación activa sobre este proyecto")
        ocupados = sum(x.get("estado") in ("en_cola", "procesando")
                       or x.get("malla") == "procesando"
                       or x.get("exportaciones") == "procesando"
                       for x in ESTADOS.values())
        if ocupados >= MAX_TRABAJOS_EN_COLA:
            raise HTTPException(429, "Servidor ocupado; esperá a que termine otro trabajo")
        carpeta = RAIZ / identificador
        if not (carpeta / "fotos").is_dir():
            raise HTTPException(404, "No se encontraron las fotografías originales")
        if shutil.which("colmap") is None:
            raise HTTPException(503, "El motor COLMAP no está disponible; instalalo antes de reintentar")
        fotos_guardadas = [p for p in (carpeta / "fotos").iterdir()
                          if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}]
        if len(fotos_guardadas) < 3:
            raise HTTPException(409, "Faltan fotografías originales; se requieren al menos tres para reintentar")
        usuario = registro.get("user_id")
        nuevo_evento_uso = uuid.uuid4().hex if usuario else None
        if usuario:
            try:
                permisos = obtener_entitlements(usuario)
                if registro.get("solicitar_denso") and not permisos["capacidades"]["reconstruccion_densa_remota"]:
                    raise PermissionError("La reconstrucción densa remota requiere plan PRO activo")
                reservar_trabajo(usuario, nuevo_evento_uso)
            except (KeyError, PermissionError, ValueError) as exc:
                raise HTTPException(403, str(exc)) from exc
        try:
            shutil.rmtree(carpeta / "resultado", ignore_errors=False)
        except FileNotFoundError:
            pass
        except OSError as exc:
            if usuario:
                try:
                    finalizar_trabajo(usuario, nuevo_evento_uso, exito=False)
                except ValueError:
                    pass
            raise HTTPException(500, "No se pudieron limpiar los resultados parciales") from exc
        try:
            # COLMAP exige que la carpeta de salida todavía no exista.
            registro.update({
                "estado": "en_cola",
                "usage_event_id": nuevo_evento_uso,
                "malla": "pendiente",
                "exportaciones": "pendiente",
                "reconstruccion_densa": "pendiente" if registro.get("solicitar_denso") else "no_solicitada",
                "error": None,
                "error_reconstruccion_densa": None,
                "error_malla": None,
                "error_exportaciones": None,
                "archivo_nube": None,
                "informe_malla": None,
                "alpha_malla": None,
                "exportaciones_formatos": [],
                "exportaciones_paquete": False,
                "cancelacion_solicitada": False,
            })
            evento_cancelacion = threading.Event()
            CANCELACIONES[identificador] = evento_cancelacion
            _guardar_estado(identificador)
        except Exception as exc:
            CANCELACIONES.pop(identificador, None)
            if usuario:
                try:
                    finalizar_trabajo(usuario, nuevo_evento_uso, exito=False)
                except ValueError:
                    pass
            raise HTTPException(500, "No se pudo reiniciar el proyecto") from exc
    try:
        threading.Thread(target=_procesar,
                         args=(identificador, carpeta, evento_cancelacion),
                         daemon=True).start()
    except Exception as exc:
        with CERROJO:
            CANCELACIONES.pop(identificador, None)
            registro["estado"] = "error"
            _guardar_estado(identificador)
        if usuario:
            try:
                finalizar_trabajo(usuario, nuevo_evento_uso, exito=False)
            except ValueError:
                pass
        raise HTTPException(500, "No se pudo iniciar el reintento") from exc
    return _estado_publico(registro)


@app.get("/api/proyectos/{identificador}/cola-persistente")
def estado_cola_persistente(identificador: str, request: Request):
    """Estado experimental de worker; solo para proyectos propios autenticados.

    No habilita procesamiento remoto ni sustituye los estados de la API.
    """
    if os.environ.get("ESCANEO3D_WORKER_STATUS_ENABLED", "").lower() not in ("1", "true", "yes"):
        raise HTTPException(404, "Consulta de worker no habilitada")
    if os.environ.get("ESCANEO3D_AUTH_REQUIRED", "").lower() not in ("1", "true", "yes"):
        raise HTTPException(503, "Se requiere autenticación para consultar workers")
    usuario = getattr(request.state, "user_id", None)
    if not usuario:
        raise HTTPException(401, "Autenticación requerida")
    with CERROJO:
        registro = ESTADOS.get(identificador)
        if not registro or registro.get("user_id") != usuario:
            raise HTTPException(404, "Proyecto no encontrado")
    base = Path(os.environ.get("ESCANEO3D_WORKER_DATA", str(RAIZ / "_workers")))
    estado = consultar_trabajo(base, identificador, usuario)
    if estado is None:
        raise HTTPException(404, "Trabajo no registrado en la cola persistente")
    return {"id": identificador, **estado, "modo": "experimental_solo_lectura"}


@app.get("/api/proyectos/{identificador}")
def estado_proyecto(identificador: str):
    with CERROJO:
        if identificador not in ESTADOS:
            raise HTTPException(404, "Proyecto no encontrado")
        return _estado_publico(ESTADOS[identificador])


@app.get("/api/proyectos/{identificador}/informe-captura")
def informe_captura_proyecto(identificador: str):
    with CERROJO:
        if identificador not in ESTADOS:
            raise HTTPException(404, "Proyecto no encontrado")
    ruta = RAIZ / identificador / "informe_captura.json"
    if not ruta.is_file():
        raise HTTPException(404, "Informe de captura no disponible")
    return FileResponse(ruta, filename="escaneo3d_informe_captura.json",
                        media_type="application/json")


def _nube_utilizable(archivo):
    from tools.motor_colmap import _ply_con_vertices
    return archivo.is_file() and _ply_con_vertices(archivo)


def _nube_preferida(identificador):
    """Resuelve la nube producida realmente, sin suponer modelo COLMAP 0."""
    resultado = RAIZ / identificador / "resultado"
    registro = ESTADOS.get(identificador, {})
    relativo = registro.get("archivo_nube")
    if isinstance(relativo, str) and relativo:
        if relativo.startswith("dense_") and registro.get("reconstruccion_densa") != "completada":
            relativo = None
    if isinstance(relativo, str) and relativo:
        candidato = (resultado / relativo).resolve()
        if candidato.is_relative_to(resultado.resolve()) and _nube_utilizable(candidato):
            return candidato
    densas = (sorted(resultado.glob("dense_*/fused.ply"))
              if registro.get("reconstruccion_densa") == "completada" else [])
    from tools.motor_colmap import _cantidad_vertices_ply
    dispersas = sorted(resultado.glob("modelo_*.ply"),
                       key=_cantidad_vertices_ply, reverse=True)
    for archivo in [*densas, *dispersas]:
        if _nube_utilizable(archivo):
            return archivo
    return None


@app.get("/api/proyectos/{identificador}/nube/vista")
def vista_nube(identificador: str):
    """Muestra limitada para inspeccionar la nube aun si falla la malla."""
    with CERROJO:
        registro = ESTADOS.get(identificador)
        if not registro or registro.get("estado") != "completado":
            raise HTTPException(404, "Nube no disponible")
    nube = _nube_preferida(identificador)
    if nube is None:
        raise HTTPException(404, "Nube no disponible")
    from tools.leer_colmap_ply import leer_nube_colmap_ply
    try:
        puntos = leer_nube_colmap_ply(nube, max_puntos=12000, submuestrear=True)
    except (ValueError, OSError) as exc:
        raise HTTPException(422, "Nube PLY no interpretable") from exc
    if not len(puntos):
        raise HTTPException(422, "La nube no contiene puntos para visualizar")
    return {"puntos": puntos.tolist(), "cantidad_muestra": len(puntos),
            "advertencia": "Vista de puntos sin superficie ni escala métrica."}


@app.get("/api/proyectos/{identificador}/nube")
def descargar_nube(identificador: str):
    with CERROJO:
        estado = ESTADOS.get(identificador)
    if not estado or estado["estado"] != "completado":
        raise HTTPException(404, "Nube no disponible")
    resultado = RAIZ / identificador / "resultado"
    archivo = _nube_preferida(identificador)
    if archivo is None:
        raise HTTPException(404, "Nube no disponible")
    return FileResponse(archivo, filename="escaneo3d_nube.ply",
                        media_type="application/octet-stream")



@app.post("/api/proyectos/{identificador}/malla", status_code=202)
def generar_malla(identificador: str, alpha: float | None = None):
    """Construye OBJ experimental desde la nube COLMAP."""
    import math
    if alpha is not None and (not math.isfinite(alpha) or alpha <= 0):
        raise HTTPException(400, "Alpha inválido")
    with CERROJO:
        registro = ESTADOS.get(identificador)
        if not registro or registro["estado"] != "completado":
            raise HTTPException(409, "Reconstrucción no completada")
        if registro.get("malla") in ("procesando", "completada"):
            raise HTTPException(409, "Malla ya iniciada")
        nube = _nube_preferida(identificador)
        if nube is None:
            raise HTTPException(409, "La nube COLMAP no está disponible; reintentá la reconstrucción")
        registro["malla"] = "procesando"
        registro["error_malla"] = None
        _guardar_estado(identificador)
    carpeta = RAIZ / identificador / "resultado"
    nubes = [nube]

    def ejecutar():
        try:
            # Un intento fallido puede dejar OBJ/informes parciales: permitir reintento.
            for nombre in ("malla_original.obj", "malla_original.informe.json",
                           "malla.obj", "malla.informe.json"):
                (carpeta / nombre).unlink(missing_ok=True)
            alpha_usado = alpha
            if alpha_usado is None:
                from tools.leer_colmap_ply import leer_nube_colmap_ply
                puntos = leer_nube_colmap_ply(nubes[0], max_puntos=2_000, submuestrear=True)
                try:
                    alpha_usado = _estimar_alpha_puntos(puntos)
                except ValueError:
                    # Un muestreo degenerado no debe impedir el respaldo convexo.
                    import numpy as np
                    extension = np.ptp(puntos, axis=0)
                    alpha_usado = max(float(np.max(extension)), 1e-9)
            malla_original = carpeta / "malla_original.obj"
            malla_reparada = carpeta / "malla.obj"
            informe_malla = nube_colmap_a_malla(
                nubes[0], malla_original, alpha_usado,
                max_puntos=2_000, submuestrear=True
            )
            informe_reparacion = reparar_obj(malla_original, malla_reparada)
            if not malla_reparada.is_file() or malla_reparada.stat().st_size == 0:
                raise RuntimeError("La reconstrucción no produjo una malla OBJ descargable")
            with malla_reparada.open("r", encoding="utf-8", errors="replace") as modelo:
                vertices_obj = 0
                caras_obj = 0
                for linea in modelo:
                    if linea.startswith("v "):
                        vertices_obj += 1
                    elif linea.startswith("f "):
                        caras_obj += 1
            if vertices_obj < 4 or caras_obj < 4:
                raise RuntimeError("La malla OBJ resultante no contiene geometría 3D suficiente")
            informe_malla["reparacion_conservadora"] = informe_reparacion
            (carpeta / "malla.informe.json").write_text(
                json.dumps(informe_malla, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            _actualizar(identificador, malla="completada",
                        alpha_malla=alpha_usado,
                        informe_malla=informe_malla)
        except Exception as exc:
            (carpeta / "malla.obj").unlink(missing_ok=True)
            (carpeta / "malla.informe.json").unlink(missing_ok=True)
            (carpeta / "malla_original.obj").unlink(missing_ok=True)
            (carpeta / "malla_original.informe.json").unlink(missing_ok=True)
            _actualizar(identificador, malla="error",
                        error_malla=f"{type(exc).__name__}: {str(exc)[:300]}")
    threading.Thread(target=_ejecutar_con_semaforo,
                     args=(ejecutar,), daemon=True).start()
    return {"id": identificador, "malla": "procesando"}




@app.get("/api/proyectos/{identificador}/paquete")
def descargar_paquete_resultados(identificador: str):
    """Empaqueta resultados generados; excluye fotografías originales."""
    with CERROJO:
        registro = ESTADOS.get(identificador)
        if not registro or registro.get("estado") != "completado":
            raise HTTPException(409, "La reconstrucción debe estar completada")
        if any(registro.get(k) == "procesando" for k in ("malla", "exportaciones")):
            raise HTTPException(409, "Esperá a que terminen la malla y las exportaciones")
    raiz = RAIZ / identificador
    resultado = raiz / "resultado"
    if not resultado.is_dir():
        raise HTTPException(404, "No hay resultados para empaquetar")
    destino = raiz / "escaneo3d_resultados.zip"
    temporal = raiz / ("paquete." + uuid.uuid4().hex + ".tmp")
    incluidos = []
    try:
        with zipfile.ZipFile(temporal, "w", compression=zipfile.ZIP_DEFLATED,
                             compresslevel=3) as paquete:
            raiz_resultados = resultado.resolve()
            for archivo in sorted(resultado.rglob("*")):
                if archivo.is_symlink() or not archivo.is_file():
                    continue
                ruta_real = archivo.resolve()
                if not ruta_real.is_relative_to(raiz_resultados):
                    continue
                if archivo != destino and archivo != temporal:
                    relativo = archivo.relative_to(resultado)
                    paquete.write(archivo, arcname=str(relativo))
                    with archivo.open("rb") as fuente:
                        sha256 = hashlib.file_digest(fuente, "sha256").hexdigest()
                    incluidos.append({
                        "archivo": str(relativo),
                        "bytes": archivo.stat().st_size,
                        "sha256": sha256,
                    })
            paquete.writestr(
                "MANIFEST.json",
                json.dumps({"archivos": incluidos, "fotos_originales_incluidas": False},
                           ensure_ascii=False, indent=2),
            )
            paquete.writestr(
                "LEEME.txt",
                "ESCANEO 3D - Paquete de resultados\\n"
                "Incluye los archivos generados por la reconstrucción.\\n"
                "No incluye fotografías originales.\\n"
                "Las unidades y la precisión dimensional no están verificadas.\\n"
                "Un STL exportado no certifica imprimibilidad.\\n"
            )
        if not incluidos:
            raise HTTPException(404, "No hay archivos generados para empaquetar")
        os.replace(temporal, destino)
    except HTTPException:
        temporal.unlink(missing_ok=True)
        raise
    except Exception as exc:
        temporal.unlink(missing_ok=True)
        raise HTTPException(500, "No se pudo preparar el paquete de resultados") from exc
    return FileResponse(destino, filename="escaneo3d_resultados.zip",
                        media_type="application/zip")


@app.get("/api/proyectos/{identificador}/malla/informe")
def descargar_informe_malla(identificador: str):
    with CERROJO:
        registro = ESTADOS.get(identificador)
        disponible = registro and registro.get("malla") == "completada"
    ruta = RAIZ / identificador / "resultado" / "malla.informe.json"
    if not disponible or not ruta.is_file():
        raise HTTPException(404, "Informe de malla no disponible")
    return FileResponse(ruta, filename="escaneo3d_informe_malla.json",
                        media_type="application/json")


@app.get("/api/proyectos/{identificador}/malla/original")
def descargar_malla_original(identificador: str):
    """Descarga la superficie alpha-shape antes de la reparación conservadora."""
    with CERROJO:
        registro = ESTADOS.get(identificador)
        disponible = registro and registro.get("malla") == "completada"
    ruta = RAIZ / identificador / "resultado" / "malla_original.obj"
    if not disponible or not ruta.is_file():
        raise HTTPException(404, "Malla original no disponible")
    return FileResponse(ruta, filename="escaneo3d_malla_original.obj",
                        media_type="application/octet-stream")


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



def _sha256_archivo(ruta):
    digest = hashlib.sha256()
    with Path(ruta).open("rb") as fuente:
        for bloque in iter(lambda: fuente.read(1024 * 1024), b""):
            digest.update(bloque)
    return digest.hexdigest()


@app.post("/api/proyectos/{identificador}/exportaciones", status_code=202)
def preparar_exportaciones(identificador: str, formatos: list[str] = Form(...),
                           crear_paquete: bool = Form(False)):
    """Prepara solo los formatos elegidos por la persona usuaria."""
    permitidos = {"obj", "ply", "stl", "glb", "3mf", "nube"}
    elegidos = tuple(dict.fromkeys(str(x).lower() for x in formatos))
    if not elegidos or any(x not in permitidos for x in elegidos):
        raise HTTPException(400, "Elegí al menos un formato disponible: OBJ, PLY, STL, GLB, 3MF o nube PLY")
    with CERROJO:
        registro = ESTADOS.get(identificador)
        if not registro or registro.get("estado") != "completado":
            raise HTTPException(409, "Primero completá la reconstrucción COLMAP")
        if any(formato != "nube" for formato in elegidos) and registro.get("malla") != "completada":
            raise HTTPException(409, "Primero generá la malla OBJ para exportar superficies")
        if registro.get("exportaciones") == "procesando":
            raise HTTPException(409, "Ya hay una exportación en curso")
        if any(formato != "nube" for formato in elegidos):
            malla = RAIZ / identificador / "resultado" / "malla.obj"
            if not malla.is_file() or malla.stat().st_size == 0:
                raise HTTPException(409, "La malla OBJ no existe o está vacía; regenerala antes de exportar")
        estado_anterior = {
            "formatos": registro.get("exportaciones_formatos", []),
            "paquete": bool(registro.get("exportaciones_paquete")),
        }
        habia_exportaciones = (
            registro.get("exportaciones") == "completadas"
            and (RAIZ / identificador / "resultado" / "exportaciones").is_dir()
        )
        registro["exportaciones"] = "procesando"
        registro["exportaciones_formatos"] = list(elegidos)
        _guardar_estado(identificador)
    carpeta = RAIZ / identificador / "resultado"
    def ejecutar():
        temporal = carpeta / ("exportaciones_tmp_" + uuid.uuid4().hex)
        respaldo = carpeta / ("exportaciones_old_" + uuid.uuid4().hex)
        nueva_instalada = False
        try:
            formatos_malla = tuple(x for x in elegidos if x != "nube")
            destino_exportaciones = temporal
            if formatos_malla:
                exportar_formatos(carpeta / "malla.obj", destino_exportaciones,
                                  formatos=formatos_malla)
            else:
                destino_exportaciones.mkdir(parents=True, exist_ok=False)
            if "nube" in elegidos:
                fuente_nube = _nube_preferida(identificador)
                if fuente_nube is None:
                    raise FileNotFoundError("No existe nube PLY original para exportar")
                shutil.copy2(fuente_nube, destino_exportaciones / "nube.ply")
            manifiesto = {
                "proyecto_id": identificador,
                "formatos_solicitados": list(elegidos),
                "archivos": [
                    {"archivo": archivo.name, "bytes": archivo.stat().st_size,
                     "sha256": _sha256_archivo(archivo)}
                    for archivo in sorted(destino_exportaciones.iterdir())
                    if archivo.is_file() and archivo.name != "informe_exportacion.json"
                ],
                "advertencia": "Las unidades físicas y la precisión dimensional no están verificadas por el formato."
            }
            (destino_exportaciones / "informe_exportacion.json").write_text(
                json.dumps(manifiesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            if crear_paquete:
                ruta_zip = destino_exportaciones / "escaneo3d_paquete.zip"
                with zipfile.ZipFile(ruta_zip, "w", compression=zipfile.ZIP_DEFLATED,
                                     compresslevel=6) as paquete:
                    for archivo in sorted(destino_exportaciones.iterdir()):
                        if archivo.is_file() and archivo != ruta_zip:
                            paquete.write(archivo, arcname=archivo.name)
            destino_final = carpeta / "exportaciones"
            if destino_final.exists():
                os.replace(destino_final, respaldo)
            try:
                os.replace(destino_exportaciones, destino_final)
                nueva_instalada = True
            except Exception:
                if respaldo.exists() and not destino_final.exists():
                    os.replace(respaldo, destino_final)
                raise
            _actualizar(identificador, exportaciones="completadas",
                        exportaciones_formatos=list(elegidos),
                        exportaciones_paquete=bool(crear_paquete),
                        error_exportaciones=None)
            shutil.rmtree(respaldo, ignore_errors=True)
        except Exception as exc:
            shutil.rmtree(temporal, ignore_errors=True)
            if nueva_instalada:
                shutil.rmtree(carpeta / "exportaciones", ignore_errors=True)
            if respaldo.exists() and not (carpeta / "exportaciones").exists():
                os.replace(respaldo, carpeta / "exportaciones")
            if habia_exportaciones and (carpeta / "exportaciones").is_dir():
                _actualizar(
                    identificador, exportaciones="completadas",
                    exportaciones_formatos=estado_anterior["formatos"],
                    exportaciones_paquete=estado_anterior["paquete"],
                    error_exportaciones=f"No se reemplazaron los archivos anteriores: {type(exc).__name__}: {str(exc)[:250]}",
                )
            else:
                _actualizar(identificador, exportaciones="error",
                            error_exportaciones=f"{type(exc).__name__}: {str(exc)[:300]}")
    threading.Thread(target=_ejecutar_con_semaforo,
                     args=(ejecutar,), daemon=True).start()
    return {"id": identificador, "exportaciones": "procesando",
            "formatos": list(elegidos)}


@app.get("/api/proyectos/{identificador}/exportaciones/paquete")
def descargar_paquete_exportacion(identificador: str):
    with CERROJO:
        registro = ESTADOS.get(identificador)
        disponible = registro and registro.get("exportaciones") == "completadas" and registro.get("exportaciones_paquete")
    ruta = RAIZ / identificador / "resultado" / "exportaciones" / "escaneo3d_paquete.zip"
    if not disponible or not ruta.is_file():
        raise HTTPException(404, "Paquete ZIP no disponible")
    return FileResponse(ruta, filename="escaneo3d_paquete.zip",
                        media_type="application/zip")


@app.get("/api/proyectos/{identificador}/exportaciones/informe")
def descargar_informe_exportacion(identificador: str):
    """Entrega tamaños, checksums y advertencias de los formatos generados."""
    with CERROJO:
        registro = ESTADOS.get(identificador)
        disponible = registro and registro.get("exportaciones") == "completadas"
    ruta = RAIZ / identificador / "resultado" / "exportaciones" / "informe_exportacion.json"
    if not disponible or not ruta.is_file():
        raise HTTPException(404, "Informe de exportación no disponible")
    return FileResponse(ruta, filename="escaneo3d_informe_exportacion.json",
                        media_type="application/json")


@app.get("/api/proyectos/{identificador}/exportaciones/{formato}")
def descargar_exportacion(identificador: str, formato: str):
    if formato not in ("obj", "ply", "stl", "glb", "3mf", "nube"):
        raise HTTPException(400, "Formato no admitido")
    with CERROJO:
        registro = ESTADOS.get(identificador)
        disponible = registro and registro.get("exportaciones") == "completadas"
    nombre_archivo = "nube.ply" if formato == "nube" else "modelo." + formato
    ruta = RAIZ / identificador / "resultado" / "exportaciones" / nombre_archivo
    if not disponible or not ruta.is_file():
        raise HTTPException(404, "Exportación no disponible")
    descarga = "escaneo3d_nube_puntos.ply" if formato == "nube" else "escaneo3d_modelo." + formato
    return FileResponse(ruta, filename=descarga,
                        media_type="application/octet-stream")



@app.patch("/api/proyectos/{identificador}/nombre")
def renombrar_proyecto(identificador: str, nombre: str = Form(...)):
    """Renombra un proyecto sin modificar fotografías ni resultados."""
    nombre = nombre.strip()
    if not 1 <= len(nombre) <= 80:
        raise HTTPException(400, "El nombre debe tener entre 1 y 80 caracteres")
    with CERROJO:
        registro = ESTADOS.get(identificador)
        if not registro:
            raise HTTPException(404, "Proyecto no encontrado")
        registro["nombre"] = nombre
        registro["actualizado_en"] = datetime.now(timezone.utc).isoformat()
        _guardar_estado(identificador)
        return registro.copy()


@app.post("/api/proyectos/{identificador}/duplicar", status_code=201)
def duplicar_proyecto(identificador: str):
    """Crea una copia independiente de fotos, resultados y metadatos del proyecto."""
    with CERROJO:
        original = ESTADOS.get(identificador)
        if not original:
            raise HTTPException(404, "Proyecto no encontrado")
        if original.get("estado") in ("en_cola", "procesando") or any(
            original.get(k) == "procesando" for k in ("malla", "exportaciones")
        ):
            raise HTTPException(409, "Esperá a que terminen los trabajos antes de duplicar")
        origen = RAIZ / identificador
        nuevo_id = uuid.uuid4().hex
        destino = RAIZ / nuevo_id
        try:
            destino.mkdir(parents=True, exist_ok=False)
            for subcarpeta in ("fotos", "resultado"):
                fuente = origen / subcarpeta
                if fuente.is_dir():
                    shutil.copytree(
                        fuente, destino / subcarpeta,
                        ignore=lambda raiz, nombres: [
                            nombre for nombre in nombres
                            if (Path(raiz) / nombre).is_symlink()
                        ],
                    )
            informe = origen / "informe_captura.json"
            if informe.is_file():
                shutil.copy2(informe, destino / informe.name)
            copia = original.copy()
            copia.update({
                "id": nuevo_id,
                "nombre": (str(original.get("nombre", "Proyecto"))[:70] + " — copia")[:80],
                "creado_en": datetime.now(timezone.utc).isoformat(),
                "origen_id": identificador,
                "usage_event_id": None,
            })
            ESTADOS[nuevo_id] = copia
            _guardar_estado(nuevo_id)
            return _estado_publico(copia)
        except Exception as exc:
            ESTADOS.pop(nuevo_id, None)
            shutil.rmtree(destino, ignore_errors=True)
            raise HTTPException(500, "No se pudo duplicar el proyecto") from exc



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


@app.delete("/api/cuenta")
def borrar_cuenta(request: Request):
    """Elimina todos los proyectos y la cuenta del sujeto autenticado."""
    usuario = getattr(request.state, "user_id", None)
    if not usuario:
        raise HTTPException(401, "Autenticación requerida")
    with CERROJO:
        proyectos = [r.copy() for r in ESTADOS.values() if r.get("user_id") == usuario]
        if any(
            p.get("estado") in ("en_cola", "procesando")
            or p.get("malla") == "procesando"
            or p.get("exportaciones") == "procesando"
            for p in proyectos
        ):
            raise HTTPException(409, "Esperá a que terminen los trabajos antes de eliminar la cuenta")
        carpetas = [RAIZ / p["id"] for p in proyectos]
        try:
            for carpeta in carpetas:
                if carpeta.exists():
                    shutil.rmtree(carpeta)
        except OSError as exc:
            raise HTTPException(500, "No se pudieron eliminar todos los archivos de la cuenta") from exc
        for proyecto in proyectos:
            ESTADOS.pop(proyecto["id"], None)
    try:
        eliminar_cuenta(usuario)
    except KeyError as exc:
        raise HTTPException(404, "Cuenta no encontrada") from exc
    return {"eliminada": True, "proyectos_eliminados": len(proyectos)}


@app.get("/api/cuenta/entitlements")
def cuenta_entitlements(request: Request):
    """Devuelve plan y cuota del sujeto autenticado; nunca acepta user_id del cliente."""
    usuario = getattr(request.state, "user_id", None)
    if not usuario:
        raise HTTPException(401, "Autenticación requerida")
    try:
        return obtener_entitlements(usuario)
    except KeyError as exc:
        raise HTTPException(403, "Cuenta sin plan asignado; contactar soporte") from exc


@app.get("/api/proyectos")
def listar_proyectos(request: Request):
    with CERROJO:
        usuario = getattr(request.state, "user_id", None)
        proyectos = [_estado_publico(registro) for registro in ESTADOS.values()
                     if not usuario or registro.get("user_id") == usuario]
        proyectos.sort(key=lambda p: p.get("creado_en", ""), reverse=False)
        return {"proyectos": proyectos}

@app.patch("/api/proyectos/{identificador}")
def renombrar_proyecto(identificador: str, nombre: str = Form(...)):
    """Cambia el nombre visible sin alterar fotografías ni resultados."""
    nuevo_nombre = nombre.strip()
    if not 1 <= len(nuevo_nombre) <= 80:
        raise HTTPException(400, "El nombre debe tener entre 1 y 80 caracteres")
    with CERROJO:
        registro = ESTADOS.get(identificador)
        if registro is None:
            raise HTTPException(404, "Proyecto no encontrado")
        registro["nombre"] = nuevo_nombre
        _guardar_estado(identificador)
        return {"id": identificador, "nombre": nuevo_nombre}




_recuperar_estados()
app.mount("/", StaticFiles(directory=str(WEB), html=True), name="web")
