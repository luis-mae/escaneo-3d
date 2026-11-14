import io
import json
import base64
import hmac
import time
import hashlib
import os
import uuid
import zipfile

import pytest
from fastapi.testclient import TestClient
from PIL import Image

import tools.servidor_web as web
from tools.verificar_paquete import verificar_paquete
from tools.entitlements import configurar_cuenta


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.setattr(web, "RAIZ", tmp_path)
    monkeypatch.setattr(web, "_procesar", lambda *_args: None)
    web.ESTADOS.clear()
    with TestClient(web.app) as test_client:
        yield test_client
    web.ESTADOS.clear()


def png_valido():
    buffer = io.BytesIO()
    Image.new("RGB", (12, 12), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def jpeg_valido():
    buffer = io.BytesIO()
    Image.new("RGB", (12, 12), "white").save(buffer, format="JPEG")
    return buffer.getvalue()


def carga_png():
    contenido = png_valido()
    return [
        ("fotos", ("vista1.png", contenido, "image/png")),
        ("fotos", ("vista2.png", contenido, "image/png")),
        ("fotos", ("vista3.png", contenido, "image/png")),
    ]


def test_crea_proyecto_y_persiste_estado(cliente):
    respuesta = cliente.post(
        "/api/proyectos",
        data={"nombre": "Pieza de prueba"},
        files=carga_png(),
    )
    assert respuesta.status_code == 202
    proyecto = respuesta.json()
    assert proyecto["estado"] == "en_cola"
    assert proyecto["fotos"] == 3
    assert proyecto["creado_en"]
    assert proyecto["reconstruccion_densa"] == "no_solicitada"
    estado = cliente.get(f"/api/proyectos/{proyecto['id']}")
    assert estado.status_code == 200
    assert estado.json()["nombre"] == "Pieza de prueba"
    assert len(list((web.RAIZ / proyecto["id"] / "fotos").glob("*.png"))) == 3


def test_preflight_captura_persistido_y_descargable(cliente):
    respuesta = cliente.post(
        "/api/proyectos",
        data={"nombre": "Preflight"},
        files=carga_png(),
    )
    assert respuesta.status_code == 202
    proyecto = respuesta.json()
    resumen = proyecto["calidad_captura"]
    assert resumen["cantidad"] == 3
    assert resumen["revisar"] == 3  # Imágenes pequeñas e idénticas del fixture.
    informe = cliente.get(
        f"/api/proyectos/{proyecto['id']}/informe-captura"
    )
    assert informe.status_code == 200
    datos = informe.json()
    assert datos["cantidad"] == 3
    assert "advertencia" in datos
    assert (web.RAIZ / proyecto["id"] / "informe_captura.json").is_file()


def test_rechaza_contenido_falso_con_mime_png(cliente):
    archivos = [
        ("fotos", (f"f{i}.png", b"esto no es una imagen", "image/png"))
        for i in range(3)
    ]
    respuesta = cliente.post(
        "/api/proyectos", data={"nombre": "Carga inválida"}, files=archivos
    )
    assert respuesta.status_code == 400
    assert "imagen" in respuesta.json()["detail"].lower()
    assert not list(web.RAIZ.iterdir())


def test_rechaza_tipo_no_admitido(cliente):
    archivos = [
        ("fotos", (f"f{i}.webp", b"contenido", "image/webp"))
        for i in range(3)
    ]
    respuesta = cliente.post(
        "/api/proyectos", data={"nombre": "WebP"}, files=archivos
    )
    assert respuesta.status_code == 400
    assert "JPG o PNG" in respuesta.json()["detail"]


def test_rechaza_cantidad_incorrecta(cliente):
    respuesta = cliente.post(
        "/api/proyectos",
        data={"nombre": "Dos fotos"},
        files=[("fotos", ("una.png", png_valido(), "image/png"))] * 2,
    )
    assert respuesta.status_code == 400


def test_elimina_proyecto_terminado(cliente):
    identificador = uuid.uuid4().hex
    carpeta = web.RAIZ / identificador
    carpeta.mkdir(parents=True)
    web.ESTADOS[identificador] = {
        "id": identificador, "nombre": "Terminado", "estado": "completado"
    }
    web._guardar_estado(identificador)
    respuesta = cliente.delete(f"/api/proyectos/{identificador}")
    assert respuesta.status_code == 200
    assert respuesta.json()["eliminado"] is True
    assert not carpeta.exists()
    assert identificador not in web.ESTADOS


def test_recupera_trabajo_interrumpido_sin_perder_fecha(cliente):
    respuesta = cliente.post(
        "/api/proyectos",
        data={"nombre": "Recuperación"},
        files=carga_png(),
    )
    proyecto = respuesta.json()
    creado = proyecto["creado_en"]
    web.ESTADOS.clear()
    web._recuperar_estados()
    recuperado = cliente.get(f"/api/proyectos/{proyecto['id']}")
    assert recuperado.status_code == 200
    assert recuperado.json()["estado"] == "interrumpido"
    assert recuperado.json()["creado_en"] == creado


def test_lista_proyectos_ordenada_por_creacion(cliente):
    ids = [uuid.uuid4().hex, uuid.uuid4().hex]
    for identificador, fecha in zip(ids, ["2026-01-02T00:00:00+00:00",
                                         "2026-01-01T00:00:00+00:00"]):
        carpeta = web.RAIZ / identificador
        carpeta.mkdir(parents=True)
        web.ESTADOS[identificador] = {
            "id": identificador, "nombre": identificador,
            "estado": "completado", "creado_en": fecha,
        }
        web._guardar_estado(identificador)
    respuesta = cliente.get("/api/proyectos")
    assert respuesta.status_code == 200
    assert [p["id"] for p in respuesta.json()["proyectos"]] == [ids[1], ids[0]]


def test_solicita_reconstruccion_densa(cliente):
    respuesta = cliente.post(
        "/api/proyectos",
        data={"nombre": "Pieza densa", "solicitar_denso": "true"},
        files=carga_png(),
    )
    assert respuesta.status_code == 202
    proyecto = respuesta.json()
    assert proyecto["solicitar_denso"] is True
    assert proyecto["reconstruccion_densa"] == "pendiente"


def test_alpha_automatico_es_proporcional_al_espaciamiento():
    import numpy as np
    from tools.servidor_web import _estimar_alpha_puntos

    puntos = np.array([
        [0., 0., 0.], [1., 0., 0.], [0., 1., 0.], [0., 0., 1.],
        [1., 1., 0.], [1., 0., 1.], [0., 1., 1.], [1., 1., 1.],
    ])
    alpha = _estimar_alpha_puntos(puntos)
    escalados = _estimar_alpha_puntos(puntos * 10)
    assert alpha > 0
    assert escalados == pytest.approx(alpha * 10)


def test_alpha_automatico_rechaza_nube_invalida():
    import numpy as np
    from tools.servidor_web import _estimar_alpha_puntos

    with pytest.raises(ValueError, match="suficientes puntos"):
        _estimar_alpha_puntos(np.array([[0., 0., 0.]]))


def test_procesamiento_elige_nube_densa_si_existe(tmp_path, monkeypatch):
    identificador = uuid.uuid4().hex
    proyecto = tmp_path / identificador
    fotos = proyecto / "fotos"
    resultado = proyecto / "resultado"
    fotos.mkdir(parents=True)
    web.ESTADOS.clear()
    web.ESTADOS[identificador] = {
        "id": identificador, "nombre": "Nube densa",
        "estado": "en_cola", "solicitar_denso": True,
    }
    monkeypatch.setattr(web, "RAIZ", tmp_path)
    llamadas = {}

    def pipeline(fotos_dir, salida, denso=False):
        llamadas["denso"] = denso
        salida.mkdir(parents=True)
        (salida / "modelo_000.ply").write_bytes(b"sparse")
        densa = salida / "dense_0"
        densa.mkdir()
        (densa / "fused.ply").write_bytes(b"dense")
        return {"disperso": {"estado": "reconstruccion_dispersa"},
                "denso": {"estado": "completado"}}

    monkeypatch.setattr(web, "pipeline_colmap", pipeline)
    try:
        web._procesar(identificador, proyecto)
        estado = web.ESTADOS[identificador]
        assert llamadas["denso"] is True
        assert estado["estado"] == "completado"
        assert estado["reconstruccion_densa"] == "completada"
        assert estado["archivo_nube"] == "dense_0/fused.ply"
    finally:
        web.ESTADOS.clear()


def test_rechaza_presupuesto_total_de_pixeles(cliente, monkeypatch):
    monkeypatch.setattr(web, "MAX_PIXELES_PROYECTO", 400)
    respuesta = cliente.post(
        "/api/proyectos",
        data={"nombre": "Demasiados píxeles"},
        files=carga_png(),
    )
    assert respuesta.status_code == 400
    assert "resolución total" in respuesta.json()["detail"].lower()
    assert not list(web.RAIZ.iterdir())


def test_fallo_denso_conserva_reconstruccion_dispersa(tmp_path, monkeypatch):
    identificador = uuid.uuid4().hex
    proyecto = tmp_path / identificador
    (proyecto / "fotos").mkdir(parents=True)
    web.ESTADOS.clear()
    web.ESTADOS[identificador] = {
        "id": identificador, "nombre": "Fallback disperso",
        "estado": "en_cola", "solicitar_denso": True,
    }
    monkeypatch.setattr(web, "RAIZ", tmp_path)

    def pipeline(_fotos, salida, denso=False):
        assert denso is True
        salida.mkdir(parents=True)
        (salida / "modelo_000.ply").write_bytes(b"sparse")
        return {
            "disperso": {"estado": "reconstruccion_dispersa"},
            "error_denso": "CUDA no disponible",
        }

    monkeypatch.setattr(web, "pipeline_colmap", pipeline)
    try:
        web._procesar(identificador, proyecto)
        estado = web.ESTADOS[identificador]
        assert estado["estado"] == "completado"
        assert estado["reconstruccion_densa"] == "fallida"
        assert estado["error_reconstruccion_densa"] == "CUDA no disponible"
        assert estado["archivo_nube"] == "modelo_000.ply"
    finally:
        web.ESTADOS.clear()


def test_acepta_jpeg_real(cliente):
    contenido = jpeg_valido()
    archivos = [
        ("fotos", (f"vista{i}.jpg", contenido, "image/jpeg"))
        for i in range(3)
    ]
    respuesta = cliente.post(
        "/api/proyectos", data={"nombre": "Fotos JPEG"}, files=archivos
    )
    assert respuesta.status_code == 202
    proyecto = respuesta.json()
    assert len(list((web.RAIZ / proyecto["id"] / "fotos").glob("*.jpg"))) == 3


def test_limita_trabajos_pesados_en_cola(cliente, monkeypatch):
    monkeypatch.setattr(web, "MAX_TRABAJOS_EN_COLA", 1)
    identificador = uuid.uuid4().hex
    web.ESTADOS[identificador] = {
        "id": identificador, "nombre": "Ocupado", "estado": "procesando"
    }
    respuesta = cliente.post(
        "/api/proyectos",
        data={"nombre": "Nuevo"},
        files=carga_png(),
    )
    assert respuesta.status_code == 429
    assert "servidor ocupado" in respuesta.json()["detail"].lower()


def test_salud_informa_colmap_disponible(cliente, monkeypatch):
    monkeypatch.setattr(web.shutil, "which", lambda _nombre: "/usr/bin/colmap")
    respuesta = cliente.get("/api/salud")
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["estado"] == "listo"
    assert datos["colmap_detectado"] is True
    assert datos["limite_trabajos"] == web.MAX_TRABAJOS_EN_COLA


def test_salud_informa_motor_ausente(cliente, monkeypatch):
    monkeypatch.setattr(web.shutil, "which", lambda _nombre: None)
    respuesta = cliente.get("/api/salud")
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "motor_no_detectado"


def test_recuperacion_limpia_exportaciones_y_malla_parciales(tmp_path, monkeypatch):
    identificador = uuid.uuid4().hex
    carpeta = tmp_path / identificador
    resultado = carpeta / "resultado"
    exportaciones = resultado / "exportaciones"
    exportaciones.mkdir(parents=True)
    (resultado / "malla.obj").write_text("parcial", encoding="utf-8")
    (resultado / "malla.informe.json").write_text("{}", encoding="utf-8")
    (exportaciones / "modelo.stl").write_bytes(b"parcial")
    (carpeta / "estado.json").write_text(
        json.dumps({
            "id": identificador, "nombre": "Interrumpido",
            "estado": "completado", "malla": "procesando",
            "exportaciones": "procesando",
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(web, "RAIZ", tmp_path)
    web.ESTADOS.clear()
    web._recuperar_estados()
    estado = web.ESTADOS[identificador]
    assert estado["malla"] == "interrumpido"
    assert estado["exportaciones"] == "interrumpido"
    assert not (resultado / "malla.obj").exists()
    assert not exportaciones.exists()
    web.ESTADOS.clear()


def test_endpoint_salud_informa_capacidad_sin_rutas_sensibles(cliente, monkeypatch):
    monkeypatch.setattr(web.shutil, "which", lambda _nombre: "/usr/bin/colmap")
    respuesta = cliente.get("/api/salud")
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["estado"] == "listo"
    assert datos["colmap_detectado"] is True
    assert datos["limite_trabajos"] == web.MAX_TRABAJOS_EN_COLA
    assert "ruta" not in datos
    assert "ESCANEO3D_DATA" not in str(datos)


def test_endpoint_salud_advierte_si_falta_colmap(cliente, monkeypatch):
    monkeypatch.setattr(web.shutil, "which", lambda _nombre: None)
    respuesta = cliente.get("/api/salud")
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "motor_no_detectado"
    assert respuesta.json()["colmap_detectado"] is False


def test_descarga_informe_malla_solo_si_esta_completada(cliente):
    identificador = uuid.uuid4().hex
    carpeta = web.RAIZ / identificador / "resultado"
    carpeta.mkdir(parents=True)
    informe = carpeta / "malla.informe.json"
    informe.write_text('{"vertices": 12, "caras": 20}', encoding="utf-8")
    web.ESTADOS[identificador] = {
        "id": identificador, "estado": "completado", "malla": "completada"
    }
    respuesta = cliente.get(f"/api/proyectos/{identificador}/malla/informe")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"vertices": 12, "caras": 20}


def test_no_descarga_informe_malla_incompleto(cliente):
    identificador = uuid.uuid4().hex
    web.ESTADOS[identificador] = {
        "id": identificador, "estado": "completado", "malla": "procesando"
    }
    respuesta = cliente.get(f"/api/proyectos/{identificador}/malla/informe")
    assert respuesta.status_code == 404


def test_descarga_paquete_zip_sin_fotos_originales(cliente):
    identificador = uuid.uuid4().hex
    raiz = web.RAIZ / identificador
    resultado = raiz / "resultado"
    fotos = raiz / "fotos"
    resultado.mkdir(parents=True)
    fotos.mkdir()
    (resultado / "nube.ply").write_bytes(b"ply")
    (resultado / "malla.obj").write_text("v 0 0 0", encoding="utf-8")
    (fotos / "original.jpg").write_bytes(b"foto privada")
    secreto = raiz / "secreto.txt"
    secreto.write_text("no incluir", encoding="utf-8")
    (resultado / "enlace_secreto.txt").symlink_to(secreto)
    web.ESTADOS[identificador] = {
        "id": identificador, "estado": "completado", "malla": "completada"
    }
    respuesta = cliente.get(f"/api/proyectos/{identificador}/paquete")
    assert respuesta.status_code == 200
    paquete_local = raiz / "descarga.zip"
    paquete_local.write_bytes(respuesta.content)
    assert verificar_paquete(paquete_local)["valido"] is True
    with zipfile.ZipFile(io.BytesIO(respuesta.content)) as paquete:
        nombres = paquete.namelist()
        assert "nube.ply" in nombres
        assert "malla.obj" in nombres
        assert "LEEME.txt" in nombres
        assert "MANIFEST.json" in nombres
        manifiesto = json.loads(paquete.read("MANIFEST.json"))
        assert manifiesto["fotos_originales_incluidas"] is False
        entrada_nube = next(x for x in manifiesto["archivos"] if x["archivo"] == "nube.ply")
        assert entrada_nube["sha256"] == hashlib.sha256(paquete.read("nube.ply")).hexdigest()
        assert entrada_nube["bytes"] == 3
        leeme = paquete.read("LEEME.txt").decode("utf-8")
        assert "No incluye fotografías originales" in leeme
        assert not any("original.jpg" in n for n in nombres)
        assert not any("enlace_secreto" in n for n in nombres)


def test_paquete_rechaza_proyecto_en_proceso(cliente):
    identificador = uuid.uuid4().hex
    web.ESTADOS[identificador] = {
        "id": identificador, "estado": "completado", "malla": "procesando"
    }
    respuesta = cliente.get(f"/api/proyectos/{identificador}/paquete")
    assert respuesta.status_code == 409


def test_paquete_no_sigue_enlaces_simbolicos_fuera_de_resultados(cliente):
    identificador = uuid.uuid4().hex
    raiz = web.RAIZ / identificador
    resultado = raiz / "resultado"
    resultado.mkdir(parents=True)
    secreto = raiz / "privado.txt"
    secreto.write_text("no incluir", encoding="utf-8")
    enlace = resultado / "archivo_externo.txt"
    try:
        enlace.symlink_to(secreto)
    except (OSError, NotImplementedError):
        pytest.skip("El sistema no permite crear enlaces simbólicos")
    (resultado / "nube.ply").write_bytes(b"ply")
    web.ESTADOS[identificador] = {
        "id": identificador, "estado": "completado", "malla": "completada"
    }
    respuesta = cliente.get(f"/api/proyectos/{identificador}/paquete")
    assert respuesta.status_code == 200
    with zipfile.ZipFile(io.BytesIO(respuesta.content)) as paquete:
        nombres = paquete.namelist()
        assert "nube.ply" in nombres
        assert "archivo_externo.txt" not in nombres
        manifiesto = json.loads(paquete.read("MANIFEST.json"))
        assert all(x["archivo"] != "archivo_externo.txt" for x in manifiesto["archivos"])


def test_modo_remoto_exige_jwt_y_deja_salud_publica(cliente, monkeypatch):
    monkeypatch.setenv("ESCANEO3D_AUTH_REQUIRED", "1")
    respuesta = cliente.get("/api/proyectos")
    assert respuesta.status_code == 401
    salud = cliente.get("/api/salud")
    assert salud.status_code == 200




def _jwt_prueba(subject, secret="test-secret-which-is-longer-than-32-bytes"):
    def encode(value):
        return base64.urlsafe_b64encode(
            json.dumps(value, separators=(",", ":")).encode()
        ).decode().rstrip("=")
    header = encode({"alg": "HS256", "typ": "JWT"})
    payload = encode({
        "sub": subject, "iss": "https://identity.test",
        "aud": "escaneo3d-test", "exp": int(time.time()) + 600,
    })
    signature = base64.urlsafe_b64encode(
        hmac.new(secret.encode(), (header + "." + payload).encode(), hashlib.sha256).digest()
    ).decode().rstrip("=")
    return "Bearer " + header + "." + payload + "." + signature


def test_modo_remoto_aisla_proyectos_y_aplica_cuota(cliente, monkeypatch, tmp_path):
    monkeypatch.setenv("ESCANEO3D_AUTH_REQUIRED", "1")
    monkeypatch.setenv("ESCANEO3D_JWT_SECRET", "test-secret-which-is-longer-than-32-bytes")
    monkeypatch.setenv("ESCANEO3D_JWT_ISSUER", "https://identity.test")
    monkeypatch.setenv("ESCANEO3D_JWT_AUDIENCE", "escaneo3d-test")
    monkeypatch.setenv("ESCANEO3D_BILLING_DB", str(tmp_path / "cuotas.sqlite3"))
    configurar_cuenta("usuario-a", "FREE")
    headers_a = {"Authorization": _jwt_prueba("usuario-a")}
    headers_b = {"Authorization": _jwt_prueba("usuario-b")}
    respuesta = cliente.post(
        "/api/proyectos", headers=headers_a,
        data={"nombre": "Proyecto privado"}, files=carga_png(),
    )
    assert respuesta.status_code == 202
    proyecto = respuesta.json()
    assert proyecto["user_id"] == "usuario-a"
    assert cliente.get("/api/cuenta/entitlements", headers=headers_a).json()["disponibles"] == 4
    assert cliente.get(f"/api/proyectos/{proyecto['id']}", headers=headers_a).status_code == 200
    assert cliente.get(f"/api/proyectos/{proyecto['id']}", headers=headers_b).status_code == 404
    lista_b = cliente.get("/api/proyectos", headers=headers_b).json()["proyectos"]
    assert lista_b == []

