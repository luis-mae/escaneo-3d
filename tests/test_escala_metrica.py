import numpy as np
import pytest
from tools.escala_metrica import factor_escala, escalar_nube, leer_ply_ascii, guardar_ply_ascii


def test_escala_con_distancia_conocida():
    cloud, report = escalar_nube([[0, 0, 0], [2, 0, 0], [0, 1, 0]], [0, 0, 0], [2, 0, 0], 50)
    assert np.allclose(cloud[1], [50, 0, 0])
    assert report['factor'] == 25


@pytest.mark.parametrize('a,b,d', [([0,0,0],[0,0,0],10), ([0,0,0],[1,0,0],0), ([0,0,0],[1,0,0],float('nan'))])
def test_referencias_invalidas(a, b, d):
    with pytest.raises(ValueError):
        factor_escala(a,b,d)


def test_ply_roundtrip(tmp_path):
    p = tmp_path / 'cloud.ply'
    points = np.array([[0,1,2],[3.25,4.5,5.75]])
    guardar_ply_ascii(p, points)
    assert np.allclose(leer_ply_ascii(p), points)


def test_no_modifica_original():
    src = np.array([[1., 0., 0.], [2., 0., 0.]])
    scaled, _ = escalar_nube(src, src[0], src[1], 10)
    assert np.allclose(src[0], [1, 0, 0])
    assert np.allclose(scaled[0], [10, 0, 0])
