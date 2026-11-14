import pytest

from tools.informe_validacion import analizar_mediciones


def test_calcula_error_dimensional_por_objeto():
    datos = {
        "objetos": [
            {"nombre": "Bloque", "mediciones": [
                {"referencia_mm": 100, "medida_mm": 102},
                {"referencia_mm": 50, "medida_mm": 49},
            ]},
            {"nombre": "Soporte", "mediciones": [
                {"referencia_mm": 20, "medida_mm": 21},
            ]},
        ]
    }
    informe = analizar_mediciones(datos, tolerancia_pct=5)
    assert informe["objetos_analizados"] == 2
    assert informe["mediciones_analizadas"] == 3
    assert informe["objetos_dentro_tolerancia"] == 2
    assert informe["error_maximo_global_pct"] == pytest.approx(5)
    assert informe["resultados"][0]["mediciones"][0]["error_mm"] == 2


def test_marca_objeto_fuera_de_tolerancia():
    datos = {"objetos": [{"nombre": "Pieza", "mediciones": [
        {"referencia_mm": 100, "medida_mm": 108}
    ]}]}
    informe = analizar_mediciones(datos, tolerancia_pct=5)
    assert informe["resultados"][0]["dentro_tolerancia"] is False
    assert informe["objetos_dentro_tolerancia"] == 0


@pytest.mark.parametrize("datos", [
    {},
    {"objetos": []},
    {"objetos": [{"nombre": "Sin medidas", "mediciones": []}]},
    {"objetos": [{"nombre": "Pieza", "mediciones": [
        {"referencia_mm": 0, "medida_mm": 1}
    ]}]},
])
def test_rechaza_datos_de_validacion_incompletos(datos):
    with pytest.raises(ValueError):
        analizar_mediciones(datos)


def test_rechaza_tolerancia_invalida():
    with pytest.raises(ValueError):
        analizar_mediciones(
            {"objetos": [{"nombre": "Pieza", "mediciones": [
                {"referencia_mm": 10, "medida_mm": 10}
            ]}]},
            tolerancia_pct=0,
        )
