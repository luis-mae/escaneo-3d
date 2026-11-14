import numpy as np
import pytest
from tools.reconstruir_par_fotos import triangular_filtrado, guardar_ply


def escena():
    K = np.array([[600., 0, 320], [0, 600, 240], [0, 0, 1.]])
    R = np.eye(3)
    t = np.array([[-0.4], [0], [0]])
    xyz = np.array([[x, y, z] for x, y, z in [(-.5, -.2, 2), (.4, .1, 3), (.2, -.3, 4)]])
    def project(x):
        q = (K @ x.T).T
        return q[:, :2] / q[:, 2:3]
    return K, R, t, xyz, project(xyz), project((R @ xyz.T + t).T)


def test_triangula_geometria_sintetica():
    K, R, t, expected, a, b = escena()
    actual, mask = triangular_filtrado(a, b, K, R, t)
    assert mask.all()
    np.testing.assert_allclose(actual, expected, atol=1e-8)


def test_descarta_correspondencia_erronea():
    K, R, t, expected, a, b = escena()
    b[-1] += [100, 90]
    _, mask = triangular_filtrado(a, b, K, R, t)
    assert not mask[-1]


def test_valida_formas():
    K, R, t, _, a, b = escena()
    with pytest.raises(ValueError):
        triangular_filtrado(a, b[:2], K, R, t)


def test_exporta_ply(tmp_path):
    p = tmp_path / 'nube.ply'
    guardar_ply(p, [[1, 2, 3], [4, 5, 6]])
    s = p.read_text()
    assert 'element vertex 2' in s and '4 5 6' in s
