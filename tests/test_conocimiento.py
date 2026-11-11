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


from fixtures_niebla import sesion_niebla


def test_inicial_t0_precarga_consultas_y_antorcha_sin_activar(sesion_niebla):
    """FR-NIE-01/02/03/04/06/07: conocimiento separado de infraestructura."""
    ses = sesion_niebla
    assert ses.estado.reloj == 0
    assert ses.estado.conocimiento.sala(INICIO).estado == 'explorada'
    assert ses.estado.conocimiento.sala(VECINA).estado == 'avistada'
    assert ses.estado.conocimiento.sala(LEJANA) is None
    antes = ses.estado.a_dict()
    agenda = ses.fachada.agenda.a_lista()
    rng = ses.fachada.azar.estado()
    ses.mapa_conocido()
    ses.foto()
    assert ses.estado.a_dict() == antes
    assert ses.fachada.agenda.a_lista() == agenda
    assert ses.fachada.azar.estado() == rng
    ses.proveedor.consultas_contenido.clear()
    with ses.proveedor.solo_metadatos():
        assert ses.paso('usar antorcha')[0]
    assert ses.estado.conocimiento.sala(VECINA).estado == 'explorada'
    assert ses.estado.conocimiento.sala(LEJANA).estado == 'avistada'
    assert all(not e.activa for e in ses.estado.salas[VECINA].enemigos)
    assert all(t.armada for t in ses.estado.salas[VECINA].trampas)


def test_observar_local_y_cambio_remoto_conserva_memoria(sesion_niebla):
    """FR-NIE-05: solo observación presencial modifica memoria."""
    ses = sesion_niebla
    mapa = ses.estado.conocimiento
    mapa.revelar(VECINA, ses.proveedor.datos_sala, True)
    mapa.observar((VECINA, 'N'), False)
    ses.estado.salas[VECINA].salidas['N'].cerrada = True
    ses.paso('esperar')
    assert mapa.puerta((VECINA, 'N')) == 'abierta'
    ses.estado.sala_actual = VECINA
    ses.fachada._actualizar_conocimiento()
    assert mapa.puerta((VECINA, 'N')) == 'cerrada'
