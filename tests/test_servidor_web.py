import io
import uuid

import pytest
from fastapi.testclient import TestClient
from PIL import Image

import tools.servidor_web as web


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
        assert estado["archivo_nube"] == "modelo_000.ply"
    finally:
        web.ESTADOS.clear()
