import numpy as np
import pytest
from tools.unificar_nubes import icp, fusionar, validar


def test_icp_traslacion_pequena():
    rng = np.random.default_rng(4)
    base = rng.normal(size=(70, 3))
    movida = base + [0.03, -0.02, 0.01]
    alineada, info = icp(movida, base)
    assert np.sqrt(np.mean((alineada - base)**2)) < 1e-5
    assert info['iteraciones'] >= 1


def test_fusion_voxel_elimina_duplicados():
    a = np.array([[0., 0., 0.], [1, 0, 0], [0, 1, 0]])
    fused = fusionar([a, a + 0.0001], voxel=0.01)
    assert len(fused) == 3


def test_rechaza_nube_invalida():
    with pytest.raises(ValueError):
        validar([[1, 2, float('nan')]] * 3)


def test_voxel_invalido():
    with pytest.raises(ValueError):
        fusionar([np.eye(3)], voxel=0)
