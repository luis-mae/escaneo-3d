import numpy as np
import pytest
from tools.poses_secuencia import encadenar_poses, estimar_secuencia


def paso(R=None, t=(1, 0, 0)):
    return {'estado': 'experimental', 'rotacion': (np.eye(3) if R is None else R).tolist(), 'traslacion_direccion': list(t)}


def test_cadena_identidad():
    poses = encadenar_poses([paso(), paso()])
    assert len(poses) == 3
    assert np.allclose(poses[-1]['t'], [2, 0, 0])


def test_composicion_rotada():
    r = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
    poses = encadenar_poses([paso(), paso(r, (0, 1, 0))])
    assert np.allclose(poses[-1]['t'], [0, 2, 0])
    assert np.allclose(poses[-1]['R'], r)


def test_rechaza_pose_invalida():
    with pytest.raises(ValueError):
        encadenar_poses([paso(np.zeros((3, 3)))])


def test_rechaza_par_insuficiente():
    with pytest.raises(ValueError):
        encadenar_poses([{'estado': 'insuficiente'}])


def test_requiere_dos_fotos():
    with pytest.raises(ValueError):
        estimar_secuencia(['solo.jpg'], 900)
