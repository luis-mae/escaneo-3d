import numpy as np
import pytest
from tools.registrar_escala import estimar_similitud, transformar_puntos


def test_recupera_escala_rotacion_y_traslacion():
    a = np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1],[1,2,3]], dtype=float)
    R = np.array([[0,-1,0],[1,0,0],[0,0,1]])
    b = 2.5*(a@R.T)+[3,-4,2]
    result = estimar_similitud(a,b)
    assert result['escala'] == pytest.approx(2.5)
    assert result['rmse'] < 1e-10
    np.testing.assert_allclose(transformar_puntos(a,result), b, atol=1e-10)


def test_rechaza_puntos_colineales():
    a = [[0,0,0],[1,0,0],[2,0,0]]
    with pytest.raises(ValueError, match='degeneradas'):
        estimar_similitud(a,a)


def test_rechaza_nan():
    with pytest.raises(ValueError, match='finitas'):
        estimar_similitud([[0,0,0],[1,0,0],[0,1,float('nan')]], [[0,0,0],[1,0,0],[0,1,0]])


def test_rechaza_pocas_referencias():
    with pytest.raises(ValueError, match='tres'):
        estimar_similitud([[0,0,0],[1,0,0]], [[0,0,0],[1,0,0]])
