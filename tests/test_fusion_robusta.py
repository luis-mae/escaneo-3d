import numpy as np
import pytest
from tools.fusion_robusta import fusionar


def test_fusion_recupera_transformacion_y_descarta_outlier():
    rng = np.random.default_rng(2)
    base = rng.normal(size=(35, 3))
    origen = (base - [2, -3, 1]) / 1.5
    refs_origen = np.vstack([origen[:20], [[50, 50, 50]]])
    refs_destino = np.vstack([base[:20], [[-50, -50, -50]]])
    resultado, info = fusionar([base, origen], [{'origen': refs_origen, 'destino': refs_destino}], umbral=0.01)
    np.testing.assert_allclose(resultado[35:], base, atol=1e-8)
    assert len(info['ajustes'][0]['outliers']) == 1


def test_fusion_voxel_promedia_duplicados():
    a = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]])
    b = a + [0., 0., 1.]
    resultado, info = fusionar([a, b], [{'origen': b, 'destino': a}], voxel=0.1, umbral=0.001)
    assert len(resultado) == 3
    assert info['puntos_entrada'] == 6


def test_fusion_rechaza_nube_invalida():
    a = np.eye(3)
    with pytest.raises(ValueError):
        fusionar([a, [[float('nan'), 0, 0]]], [{'origen': a, 'destino': a}])


def test_fusion_rechaza_referencias_insuficientes():
    a = np.eye(3)
    with pytest.raises(ValueError):
        fusionar([a, a], [{'origen': a[:2], 'destino': a[:2]}])
