from tools.tracks_multivista import construir_tracks


def test_cadena_tres_vistas():
    r = construir_tracks([(0, 3, 1, 8), (1, 8, 2, 5)])
    assert r['tracks'] == [{0: 3, 1: 8, 2: 5}]


def test_rechaza_conflicto_en_misma_imagen():
    r = construir_tracks([(0, 1, 1, 2), (1, 2, 2, 3), (0, 9, 2, 3)])
    assert r['correspondencias_rechazadas'] == 1
    assert {0: 1, 1: 2, 2: 3} in r['tracks']


def test_filtra_por_numero_de_vistas():
    r = construir_tracks([(0, 1, 1, 2), (1, 2, 2, 3), (3, 1, 4, 1)], minimo_vistas=3)
    assert r['total_tracks'] == 1


def test_no_admite_correspondencias_intraimagen():
    r = construir_tracks([(0, 1, 0, 2)])
    assert r['total_tracks'] == 0
    assert r['correspondencias_rechazadas'] == 1


def test_valida_minimo():
    import pytest
    with pytest.raises(ValueError):
        construir_tracks([], minimo_vistas=1)
