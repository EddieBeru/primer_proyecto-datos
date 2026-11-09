"""Conocimiento aislado: observar localmente, revelar sin contenido y no mutar al consultar."""

from fixtures_niebla import INICIO, VECINA, LEJANA, AISLADA, proveedor_niebla
from src.controller2.conocimiento import MapaConocido


def test_tres_estados_sin_fugas_y_precarga_no_revela(proveedor_niebla):
    mapa = MapaConocido()
    proveedor_niebla.sala_lista(VECINA)
    assert mapa.sala(VECINA) is None
    with proveedor_niebla.solo_metadatos():
        mapa.revelar(INICIO, proveedor_niebla.datos_sala)
    assert mapa.sala(INICIO).estado == "explorada"
    assert mapa.sala(VECINA).nombre is None
    assert mapa.sala(VECINA).salidas == ()
    assert mapa.sala(LEJANA) is None
    revision = mapa.revision
    assert mapa.a_dict() == mapa.a_dict()
    assert mapa.revision == revision


def test_antorcha_revela_vecinas_por_puerta_cerrada_sin_recursion(proveedor_niebla):
    mapa = MapaConocido()
    with proveedor_niebla.solo_metadatos():
        mapa.revelar(VECINA, proveedor_niebla.datos_sala, antorcha=True)
    assert mapa.sala(LEJANA).estado == "explorada"
    assert mapa.sala(AISLADA).estado == "explorada"
    assert mapa.puerta((VECINA, "N")) == "desconocida"
    assert proveedor_niebla.activaciones == []
    assert proveedor_niebla.consultas_contenido == []


def test_revelacion_remota_conserva_memoria_y_repetir_no_duplica(proveedor_niebla):
    mapa = MapaConocido()
    mapa.observar((VECINA, "N"), False)
    mapa.revelar(INICIO, proveedor_niebla.datos_sala, antorcha=True)
    assert mapa.puerta((VECINA, "N")) == "abierta"
    assert mapa.sala(LEJANA).estado == "avistada"
    revision = mapa.revision
    assert mapa.revelar(INICIO, proveedor_niebla.datos_sala, antorcha=True) == []
    assert mapa.revision == revision


def test_reversion_de_cambios_restaurando_ausencia(proveedor_niebla):
    mapa = MapaConocido()
    inicial = mapa.a_dict()
    cambios = mapa.revelar(INICIO, proveedor_niebla.datos_sala, antorcha=True)
    cambios += mapa.observar((INICIO, "E"), False)
    for cambio in reversed(cambios):
        mapa.aplicar(cambio, adelante=False)
    assert mapa.a_dict() == inicial
    for cambio in cambios:
        mapa.aplicar(cambio)
    assert mapa.sala(INICIO).estado == "explorada"
