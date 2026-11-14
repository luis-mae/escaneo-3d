import numpy as np
import pytest
from tools.registrar_escala_robusta import estimar_similitud_robusta


def test_outliers_separados_y_escala_recuperada():
    rng = np.random.default_rng(11)
    a = rng.normal(size=(30, 3))
    b = 2.4 * a + np.array([3., -2., 1.])
    b[::5] += 50
    r = estimar_similitud_robusta(a, b, umbral=0.001, semilla=4)
    assert abs(r['escala'] - 2.4) < 1e-8
    assert set(r['outliers']) == set(range(0, 30, 5))
    assert r['rmse_inliers'] < 1e-8


def test_rechaza_parametros_invalidos():
    a = np.eye(3)
    with pytest.raises(ValueError):
        estimar_similitud_robusta(a, a, umbral=0)


def test_rechaza_datos_sin_consenso():
    rng = np.random.default_rng(1)
    a = rng.normal(size=(12, 3))
    b = rng.normal(size=(12, 3))
    with pytest.raises(ValueError):
        estimar_similitud_robusta(a, b, umbral=1e-7, minimo_inliers=5)
