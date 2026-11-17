import pytest
from fixtures_niebla import INICIO, VECINA, LEJANA, sesion_niebla


def preparar(ses):
    ses.estado.conocimiento.revelar(INICIO, ses.proveedor.datos_sala, antorcha=True)
    ses.estado.salas[VECINA].enemigos.clear()
    ses.estado.salas[VECINA].trampas.clear()


def test_controles_sin_tiempo_destino_actual_y_no_explorada(sesion_niebla):
    """FR-NIE-10/12: destino no explorado sin tiempo (Apéndice B)."""
    ses = sesion_niebla
    antes = (ses.foto().conocimiento_revision, ses.estado.reloj, ses.fachada.agenda.a_lista(), ses.estado.acciones_jugador)
    assert not ses.paso("ir a 5")[0]
    assert not ses.paso("ir a nope")[0]
    assert ses.paso("ir a 2")[0]
    assert antes == (ses.foto().conocimiento_revision, ses.estado.reloj, ses.fachada.agenda.a_lista(), ses.estado.acciones_jugador)


def test_paso_individual_consultas_y_cancelacion(sesion_niebla):
    ses = sesion_niebla
    preparar(ses)
    assert ses.paso("ir a 5")[0]
    assert ses.paso("mapa")[0] and ses.foto().viaje["activo"]
    assert ses.avanzar_viaje()[0]
    assert ses.estado.sala_actual == VECINA
    assert ses.estado.acciones_jugador == 1
    assert ses.foto().viaje["motivo"] == "destino"
    antes = ses.estado.reloj
    ses.paso("cancelar")
    ses.avanzar_viaje()
    assert ses.estado.reloj == antes


def test_enemigos_vivos_iniciales_rechazan_y_actual_termina(sesion_niebla):
    ses = sesion_niebla
    preparar(ses)
    enemigo = ses.proveedor.sala_lista(LEJANA).enemigos[0]
    ses.estado.salas[INICIO].enemigos.append(enemigo)
    assert not ses.paso("ir a 5")[0]
    assert ses.paso("ir a 2")[0]
    enemigo.vida_actual = 0
    assert ses.paso("ir a 5")[0]


def test_dormidos_al_entrar_detienen_aunque_mueran_en_drenaje(sesion_niebla, monkeypatch):
    ses = sesion_niebla
    ses.estado.conocimiento.revelar(INICIO, ses.proveedor.datos_sala, antorcha=True)
    assert ses.paso("ir a 5")[0]
    def drenar():
        for enemigo in ses.estado.salas[VECINA].enemigos:
            enemigo.vida_actual = 0
    monkeypatch.setattr(ses, "_drenar", drenar)
    ses.avanzar_viaje()
    assert ses.foto().viaje["motivo"] == "dano"  # trampa, aun antes del drenaje


@pytest.mark.parametrize("origen", ["ataque", "trampa", "veneno", "quemadura"])
def test_dano_curado_no_se_pierde(sesion_niebla, monkeypatch, origen):
    ses = sesion_niebla
    preparar(ses)
    ses.paso("ir a 5")
    def drenar():
        ses.estado.jugador.recibir_dano(2)
        ses.estado.jugador.curar(2)
    monkeypatch.setattr(ses, "_drenar", drenar)
    ses.avanzar_viaje()
    assert ses.estado.jugador.vida_actual == 100
    assert ses.foto().viaje["motivo"] == "dano"


def test_puerta_cerrada_no_abre_aun_con_llave(sesion_niebla):
    """FR-NIE-05/13/14/15: memoria desactualizada sin apertura automática (Apéndice B)."""
    ses = sesion_niebla
    preparar(ses)
    ses.estado.conocimiento.revelar(VECINA, ses.proveedor.datos_sala, antorcha=True)
    ses.estado.conocimiento.observar((VECINA,"N"), False)
    ses.paso("ir a 1000000000000")
    ses.avanzar_viaje()
    antes = ses.estado.reloj
    ses.avanzar_viaje()
    assert ses.estado.reloj == antes
    assert ses.estado.salas[VECINA].salidas["N"].cerrada
    assert ses.foto().viaje["motivo"] == "sin_ruta"


def test_cancelar_en_sala_intermedia_no_ejecuta_otro_paso(sesion_niebla):
    """FR-NIE-21: cancelación entre pasos sin consumir tiempo."""
    ses = sesion_niebla
    preparar(ses)
    ses.estado.conocimiento.revelar(VECINA, ses.proveedor.datos_sala, antorcha=True)
    ses.estado.salas[VECINA].salidas["N"].cerrada = False
    ses.estado.conocimiento.observar((VECINA,"N"), False)
    ses.paso(f"ir a {LEJANA}")
    ses.avanzar_viaje()
    assert ses.estado.sala_actual == VECINA and ses.foto().viaje["activo"]
    reloj = ses.estado.reloj
    ses.paso("cancelar")
    ses.avanzar_viaje()
    assert ses.estado.sala_actual == VECINA and ses.estado.reloj == reloj


def test_orden_comentario_una_vez_y_pasos_individuales(sesion_niebla):
    """FR-NIE-16: comentario por orden y movimiento por paso."""
    ses = sesion_niebla
    preparar(ses)
    ses.paso("ir a 5")
    ses.avanzar_viaje()
    assert ses._mem.leer().count("#ir-a 5") == 1
    assert sum("|mover|jugador|" in l for l in ses._mem.leer()) == 1


def test_dormidos_muertos_durante_drenaje_sin_dano_detienen_por_enemigos(sesion_niebla, monkeypatch):
    """FR-NIE-12/14: entrar con dormidos detiene aun si mueren después (Apéndice B)."""
    ses = sesion_niebla
    ses.estado.conocimiento.revelar(INICIO, ses.proveedor.datos_sala, True)
    ses.estado.salas[VECINA].trampas.clear()
    assert ses.paso('ir a 5')[0]
    def drenar():
        for enemigo in ses.estado.salas[VECINA].enemigos:
            enemigo.vida_actual = 0
    monkeypatch.setattr(ses, '_drenar', drenar)
    ses.avanzar_viaje()
    assert ses.foto().viaje['motivo'] == 'enemigos'


def test_error_de_contenido_detiene_sin_cobrar(sesion_niebla, monkeypatch):
    ses = sesion_niebla
    preparar(ses)
    assert ses.paso('ir a 5')[0]
    reloj = ses.estado.reloj
    def fallar(_):
        raise RuntimeError('contenido no disponible')
    del ses.estado.salas[VECINA]
    monkeypatch.setattr(ses.proveedor, 'sala_lista', fallar)
    ses.avanzar_viaje()
    assert not ses.foto().viaje['activo']
    assert ses.foto().viaje['motivo'] == 'error'
    assert ses.estado.reloj == reloj


@pytest.mark.parametrize('tipo', ['veneno', 'quemadura'])
def test_evento_real_de_efecto_detiene_viaje_aunque_luego_se_cure(sesion_niebla, tipo):
    ses = sesion_niebla
    preparar(ses)
    ses.estado.jugador.efectos[tipo] = 1000
    ses.fachada.agenda.programar(1, tipo, {'dano': 2})
    assert ses.paso('ir a 5')[0]
    ses.avanzar_viaje()
    assert ses.foto().viaje['motivo'] == 'dano'
    assert ses.estado.jugador.vida_actual < 100


def test_pergamino_revierte_solo_ultimo_paso_y_cancela(sesion_niebla):
    """FR-NIE-17/21: pergamino durante viaje revierte un paso (Apéndice B)."""
    ses = sesion_niebla
    preparar(ses)
    ses.estado.conocimiento.revelar(VECINA, ses.proveedor.datos_sala, True)
    ses.estado.salas[VECINA].salidas['E'].cerrada = False
    ses.estado.conocimiento.observar((VECINA, 'E'), False)
    assert ses.paso('ir a 999')[0]
    ses.avanzar_viaje()
    assert ses.estado.sala_actual == VECINA and ses.fachada.viaje.activo
    assert ses.paso('deshacer')[0]
    assert ses.estado.sala_actual == INICIO
    assert not ses.fachada.viaje.activo
    antes = ses.estado.reloj
    ses.avanzar_viaje()
    assert ses.estado.reloj == antes
