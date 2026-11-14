import numpy as np
import pytest
from tools.superficie_concava import superficie_alpha


def test_tetraedro_con_alpha_grande():
    pts = [[0,0,0], [1,0,0], [0,1,0], [0,0,1]]
    v, f, n = superficie_alpha(pts, 2)
    assert len(v) == 4 and len(f) == 4 and n == 1


def test_alpha_pequeno_excluye_tetraedro():
    _, f, n = superficie_alpha([[0,0,0],[1,0,0],[0,1,0],[0,0,1]], .1)
    assert len(f) == 0 and n == 0


def test_rechaza_alpha_invalido():
    with pytest.raises(ValueError):
        superficie_alpha([[0,0,0],[1,0,0],[0,1,0],[0,0,1]], -1)


def test_orientacion_hacia_fuera():
    p, faces, _ = superficie_alpha([[0,0,0],[1,0,0],[0,1,0],[0,0,1]], 2)
    center = p.mean(axis=0)
    for a,b,c in faces:
        normal = np.cross(p[b]-p[a], p[c]-p[a])
        assert np.dot(normal, (p[a]+p[b]+p[c])/3-center) > 0
