import numpy as np
import pytest
from tools.calibracion_metrica import calibrar, puntos_en_mm

PTS = [[0,0,0],[1,0,0],[0,2,0],[0,0,3]]

def test_escala_consistente():
    r = calibrar(PTS, [{'a':0,'b':1,'mm':10},{'a':0,'b':2,'mm':20}])
    assert r['apto_para_medicion']
    assert np.allclose(puntos_en_mm(PTS,r)[1], [10,0,0])

def test_referencias_inconsistentes_bloquean_exportacion():
    r = calibrar(PTS, [{'a':0,'b':1,'mm':10},{'a':0,'b':2,'mm':40}])
    assert not r['apto_para_medicion']
    with pytest.raises(ValueError):
        puntos_en_mm(PTS,r)

def test_referencia_duplicada():
    with pytest.raises(ValueError):
        calibrar(PTS, [{'a':0,'b':1,'mm':10},{'a':1,'b':0,'mm':10}])

def test_distancia_nula():
    with pytest.raises(ValueError):
        calibrar(PTS, [{'a':0,'b':1,'mm':0},{'a':0,'b':2,'mm':20}])

def test_referencia_fuera_de_rango():
    with pytest.raises(ValueError):
        calibrar(PTS, [{'a':0,'b':9,'mm':10},{'a':0,'b':2,'mm':20}])
