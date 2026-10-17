"""Tests de todo el Controlador 2 (motor): modelo, agenda, reloj, movimiento,
inventario, combate, efectos, enemigos, deshacer, victoria, bitacora y fachada.

Un solo documento. Estilo pytest (funciones test_*), como el resto de tests/.
Se corre con:  python -m pytest tests/test_controlador.py
"""

from types import SimpleNamespace

from src.controller1.fake_provider import CRIPTA_ID, FakeProvider
from src.controller1.mergesort import mergesort
from src.controller2 import (
    Agenda,
    BitacoraMemoria,
    EnemigoInstancia,
    EstadoPartida,
    Fachada,
    Inventario,
    InventarioLlenoError,
    PilaDeshacer,
    QUEMADURA_DURACION,
    RelojVirtual,
    SalaViva,
    TrampaInstancia,
    actualizar_estado,
    aplicar_inversa,
    ataque_enemigo,
    ataque_jugador,
    calcular_puntaje,
    decidir_destino,
    deshacer_una,
    ejecutar_cierre,
    ejecutar_fin_efecto,
    ejecutar_quemadura,
    ejecutar_rearme,
    envenenar,
    formatear,
    hay_derrota,
    hay_victoria,
    intentar_mover,
    mover_enemigo,
    ordenar_puntajes,
    parsear,
    pisar_trampa,
    quemar,
    reproducir,
    turno_enemigo,
    usar_antidoto,
    usar_antorcha,
    usar_pocion,
)
from src.models.dungeons import DungeonGeneral
from src.models.roomContents import EnemyPlacement, RoomContentEntry
from src.models.rooms import Exit, Room


# ------------------------------------------------------------- ayudantes

IDS_FICHAS = [
    "esqueleto-guardian-01", "murcielago-errante-01", "sombra-rastreadora-01",
    "jefe-cripta-01", "espada-hierro-01", "escudo-madera-01", "pocion-roja-01",
    "pocion-veloz-01", "antidoto-01", "llave-hierro-01", "llave-salida-01",
    "antorcha-01", "pergamino-01", "pinchos-01", "veneno-01", "llamas-01",
]


def ficha_chica():
    return DungeonGeneral.from_dict({
        "id": "c", "version": "v1", "salas_total": 3, "paginas": 1,
        "salas_por_pagina": 50, "sala_inicial": 1, "sala_salida": 3,
        "llave_salida": "llave-sal", "presupuesto_solicitudes": 9,
        "inventario_max": 5,
        "jugador": {"vida_max": 30, "ataque": 6, "defensa": 2, "velocidad": 5},
    })


def estado_chico():
    return EstadoPartida.nueva_partida(ficha_chica(), "cat-v1")


class ProveedorVivo:
    """Adapta el FakeProvider (C1-1, SalaLista) a lo que pide C2 (K1, SalaViva)."""

    def __init__(self):
        self.fake = FakeProvider()
        self.catalogo = {i: self.fake.ficha(i) for i in IDS_FICHAS}

    def sala_lista(self, n):
        sl = self.fake.sala_lista(n)
        sv = SalaViva.desde_esqueleto(sl.room)
        sv.enemigos = [EnemigoInstancia(e.instancia, e.ficha.id, e.vida_actual, n)
                       for e in sl.enemigos]
        sv.objetos_suelo = [o.ficha.id for o in sl.objetos]
        sv.trampas = [TrampaInstancia(t.instancia, t.ficha.id, n, t.armada)
                      for t in sl.trampas]
        return sv

    def general(self):
        return self.fake.preparar_cripta(CRIPTA_ID)


def fachada_fake():
    prov = ProveedorVivo()
    est = EstadoPartida.nueva_partida(prov.general(), "fake-v1")
    est.registrar_sala(prov.sala_lista(1))
    return Fachada(est, prov, dict(prov.catalogo)), prov


def sala_simple(n=1, salidas=None):
    return SalaViva.desde_esqueleto(
        Room.from_dict({"id": n, "nombre": f"S{n}", "salidas": salidas or {}}))


# ------------------------------------------------------------- C2-1 modelo

def test_jugador_nace_lleno():
    j = estado_chico().jugador
    assert (j.vida_actual, j.vida_max) == (30, 30)
    assert j.inventario == [] and j.vivo


def test_jugador_rechaza_rangos():
    base = ficha_chica().jugador
    for malo in ({"vida_max": 0}, {"velocidad": 0}):
        d = dict(vida_max=base.vida_max, ataque=base.ataque,
                 defensa=base.defensa, velocidad=base.velocidad)
        d.update(malo)
        try:
            type(estado_chico().jugador)(**d, vida_actual=1)
            assert False, d
        except ValueError:
            pass


def test_salida_vacia_es_abierta():
    s = SalaViva.desde_esqueleto(
        Room.from_dict({"id": 1, "nombre": "A", "salidas": {"N": {"sala": 2}}}))
    assert s.salidas["N"].cerrada is False and s.salidas["N"].llave is None


def test_sala_oscura_se_hereda_y_serializa():
    """Mejoras 2026-10: campo opcional `oscura`/`oscuridad` de la API."""
    sala = Room.from_dict({"id": 7, "nombre": "Cripta", "oscuridad": True})
    assert sala.oscura is True
    assert Room.from_dict({"id": 8, "nombre": "Sala"}).oscura is False
    sv = SalaViva.desde_esqueleto(sala)
    assert sv.oscura is True
    # el contenido también puede declararla y se mezcla al hidratar
    assert RoomContentEntry.from_dict({"sala": 7, "oscuridad": True}).oscura is True
    apagada = SalaViva.desde_esqueleto(Room.from_dict({"id": 9, "nombre": "S"}))
    apagada.hidratar_contenido(RoomContentEntry.from_dict(
        {"sala": 9, "enemigos": [], "objetos": [], "trampas": [], "oscura": True}))
    assert apagada.oscura is True
    # viaja en el guardado genérico (v2)
    est = estado_chico()
    est.registrar_sala(sv)
    vuelta = EstadoPartida.desde_dict(est.a_dict())
    assert vuelta.salas[7].oscura is True


def test_puede_pasar_pide_llave():
    est = estado_chico()
    salida = SalaViva.desde_esqueleto(Room.from_dict(
        {"id": 1, "nombre": "A",
         "salidas": {"E": {"sala": 2, "cerrada": True, "llave": "k"}}}))
    ok, msg = salida.salidas["E"].puede_pasar(est.jugador)
    assert not ok and "k" in msg
    est.jugador.inventario.append("k")
    assert salida.salidas["E"].puede_pasar(est.jugador)[0]


def test_vida_vacia_usa_vida_max_del_tipo():
    e = EnemigoInstancia.desde_colocacion(
        EnemyPlacement(instancia="x", tipo="goblin", vida=None), 1, 40)
    assert e.vida_actual == 40 and e.vivo


def test_tipo_vs_instancia_independientes():
    s = sala_simple()
    s.hidratar_contenido(RoomContentEntry.from_dict(
        {"sala": 1, "enemigos": [{"instancia": "a", "tipo": "g"},
                                {"instancia": "b", "tipo": "g"}],
         "objetos": ["moneda"], "trampas": [{"instancia": "t", "tipo": "p"}]}),
        {"g": 10})
    assert len(s.enemigos) == 2 and s.objetos_suelo == ["moneda"]
    assert s.trampas[0].armada is True
    s.enemigos[0].recibir_dano(99)
    assert not s.enemigos[0].vivo and s.enemigos[1].vivo


def test_estado_roundtrip_identico():
    est = estado_chico()
    est.registrar_sala(sala_simple(1, {"E": {"sala": 2}}))
    assert EstadoPartida.desde_dict(est.a_dict()) == est


# ------------------------------------------------------------- C2-2 agenda

def test_agenda_orden_tiempo():
    ag = Agenda()
    ag.programar(10, "a", {})
    ag.programar(3, "b", {})
    assert [e.tipo for e in ag] == ["b", "a"]
    assert ag.sacar_proximo().tipo == "b" and len(ag) == 1


def test_agenda_empate_desempata_seq():
    ag = Agenda()
    e1 = ag.programar(5, "primero", {})
    e2 = ag.programar(5, "segundo", {})
    assert ag.sacar_proximo().seq == e1.seq
    assert ag.sacar_proximo().seq == e2.seq


def test_agenda_vacia():
    ag = Agenda()
    assert ag.vacia and ag.ver_proximo() is None and ag.sacar_proximo() is None


def test_agenda_cancelar_en_medio():
    ag = Agenda()
    ag.programar(1, "a", {})
    medio = ag.programar(2, "b", {})
    ag.programar(3, "c", {})
    assert ag.cancelar_por_seq(medio.seq) and not ag.cancelar_por_seq(999)
    assert [e.tipo for e in ag] == ["a", "c"]


def test_agenda_cancelar_donde():
    ag = Agenda()
    ag.programar(1, "veneno", {})
    ag.programar(2, "veneno", {})
    ag.programar(3, "turno", {})
    assert ag.cancelar_donde(lambda e: e.tipo == "veneno") == 2
    assert [e.tipo for e in ag] == ["turno"]


def test_agenda_serializa_k2_y_sigue_seq():
    ag = Agenda()
    ag.programar(7, "turno", {"actor": "g"})
    ag.programar(3, "cierre_puerta", {})
    lista = ag.a_lista()
    ag2 = Agenda.desde_lista(lista)
    assert ag2.a_lista() == lista
    nuevo = ag2.programar(9, "x", {})
    assert nuevo.seq > max(e["seq"] for e in lista)


# ------------------------------------------------------------- C2-3 reloj

def test_intervalo_menos_espera_si_mas_velocidad():
    rj = RelojVirtual()
    assert rj.intervalo(10) < rj.intervalo(5)
    try:
        rj.intervalo(0)
        assert False
    except ValueError:
        pass


def test_turnos_rapido_antes_que_lento():
    rj, ag = RelojVirtual(), Agenda()
    rj.programar_turno(ag, "lento", 5)
    rj.programar_turno(ag, "rapido", 10)
    assert rj.avanzar(ag).datos["actor"] == "rapido"
    assert rj.avanzar(ag).datos["actor"] == "lento"
    assert rj.avanzar(Agenda()) is None


def test_avanzar_pasado_es_error():
    rj, ag = RelojVirtual(ahora=10), Agenda()
    ag.programar(5, "viejo", {})
    try:
        rj.avanzar(ag)
        assert False
    except ValueError:
        pass


# ------------------------------------------------------------- C2-4 movimiento

def test_mover_sin_salida():
    est = estado_chico()
    est.registrar_sala(sala_simple())
    r = intentar_mover(est, "N", ProveedorVivo(), Agenda(), RelojVirtual())
    assert not r.ok and "camino" in r.mensaje


def test_puerta_llave_sin_y_con():
    from src.controller2.movimiento import abrir_puerta
    prov = ProveedorVivo()
    est = EstadoPartida.nueva_partida(prov.general(), "fake-v1")
    est.registrar_sala(prov.sala_lista(1))
    est.registrar_sala(prov.sala_lista(2))
    est.sala_actual = 2
    ag, rj = Agenda(), RelojVirtual()
    r = intentar_mover(est, "S", prov, ag, rj)  # 2->4 cerrada llave-hierro-01
    assert not r.ok and "llave-hierro-01" in r.mensaje
    est.jugador.inventario.append("llave-hierro-01")
    # §2.5: abrir (costo 50) y mover (costo 100) son acciones distintas.
    a = abrir_puerta(est, "S", ag, rj)
    assert a.ok
    r = intentar_mover(est, "S", prov, ag, rj)
    assert r.ok and not r.abrio_puerta and est.sala_actual == 4


def test_recorre_cripta_fake_6_salas():
    from src.controller2.movimiento import abrir_puerta
    prov = ProveedorVivo()
    est = EstadoPartida.nueva_partida(prov.general(), "fake-v1")
    est.registrar_sala(prov.sala_lista(1))
    ag, rj = Agenda(), RelojVirtual()

    def mover(direccion):
        r = intentar_mover(est, direccion, prov, ag, rj)
        assert r.ok, (direccion, r.mensaje)
        return r

    def abrir(direccion):
        a = abrir_puerta(est, direccion, ag, rj)
        assert a.ok, (direccion, a.mensaje)
        return a

    mover("E")  # 1->2
    mover("O")  # 2->1
    mover("S")  # 1->3
    est.jugador.inventario.append("llave-hierro-01")  # recoger (se prueba aparte)
    mover("E")  # 3->4
    abrir("N")  # 4->2 abre con llave
    assert mover("N").sala == 2
    abrir("S")  # 2->4 abre la otra puerta
    assert mover("S").sala == 4
    mover("S")  # 4->6
    mover("O")  # 6->5
    est.jugador.inventario.append("llave-salida-01")  # recoger (se prueba aparte)
    abrir("E")  # 5->6 abre salida
    assert mover("E").sala == 6
    assert len(est.salas_visitadas) == 6


def test_ruta_con_llaves_abre_dos_puertas():
    from src.controller2.movimiento import abrir_puerta
    prov = ProveedorVivo()
    est = EstadoPartida.nueva_partida(prov.general(), "fake-v1")
    est.registrar_sala(prov.sala_lista(1))
    ag, rj = Agenda(), RelojVirtual()
    assert intentar_mover(est, "S", prov, ag, rj).ok  # 1->3
    est.jugador.inventario.append("llave-hierro-01")
    assert intentar_mover(est, "E", prov, ag, rj).ok  # 3->4
    assert abrir_puerta(est, "N", ag, rj).ok  # 4->2 abre
    assert intentar_mover(est, "N", prov, ag, rj).ok
    assert abrir_puerta(est, "S", ag, rj).ok  # 2->4 abre (otra puerta)
    assert intentar_mover(est, "S", prov, ag, rj).ok


def test_cierre_automatico_se_programa_y_ejecuta():
    from src.controller2.movimiento import abrir_puerta

    class Prov:
        def sala_lista(self, n):
            return sala_simple(n, {"O": {"sala": 1}} if n == 2 else {})

    est = estado_chico()
    s1 = sala_simple(1, {"E": {"sala": 2, "cerrada": True, "llave": "k",
                              "cierre_automatico": 5}})
    est.registrar_sala(s1)
    est.jugador.inventario.append("k")
    ag, rj = Agenda(), RelojVirtual()
    a = abrir_puerta(est, "E", ag, rj)
    assert a.ok and a.evento_cierre_seq is not None
    r = intentar_mover(est, "E", Prov(), ag, rj)
    assert r.ok
    assert ag.ver_proximo().tipo == "cierre_puerta"
    rj.avanzar(ag)
    assert ejecutar_cierre(est, 1, "E") and s1.salidas["E"].cerrada


def test_proveedor_falla_revierte_apertura():
    class ProvRoto:
        def sala_lista(self, n):
            raise RuntimeError("sin red")

    est = estado_chico()
    s1 = sala_simple(1, {"E": {"sala": 2, "cerrada": True, "llave": "k",
                              "cierre_automatico": 5}})
    est.registrar_sala(s1)
    est.jugador.inventario.append("k")
    ag, rj = Agenda(), RelojVirtual()
    r = intentar_mover(est, "E", ProvRoto(), ag, rj)
    assert not r.ok and s1.salidas["E"].cerrada
    assert all(e.tipo != "cierre_puerta" for e in ag)


# ------------------------------------------------------------- C2-5 inventario

def test_inventario_lleno():
    inv = Inventario(2)
    inv.recoger("a")
    inv.recoger("b")
    assert inv.lleno
    try:
        inv.recoger("c")
        assert False
    except InventarioLlenoError:
        pass


def test_soltar_primero_ultimo_medio():
    inv = Inventario(5, ["a", "b", "c"])
    assert inv.soltar_en(0) == "a"
    assert inv.soltar_en(len(inv) - 1) == "c"
    inv2 = Inventario(5, ["x", "y", "z"])
    assert inv2.soltar_en(1) == "y" and inv2.a_lista() == ["x", "z"]
    try:
        Inventario(2).soltar_en(0)
        assert False
    except IndexError:
        pass


def test_equipar_fondo_al_frente():
    inv = Inventario(5, ["a", "b", "c"])
    assert inv.equipar(2) == "c" and inv.a_lista()[0] == "c"
    assert inv.equipar(0) == "c"


def test_doble_sentido():
    inv = Inventario(5, ["a", "b", "c"])
    assert list(reversed(inv)) == ["c", "b", "a"]
    assert inv.contiene("b") and not inv.contiene("z")


def test_ordenar_con_mergesort_real():
    inv = Inventario(5, ["c", "a", "b"])
    inv.ordenar(mergesort)
    assert inv.a_lista() == ["a", "b", "c"]


def test_ordenar_sin_algoritmo_falla():
    try:
        Inventario(3, ["b", "a"]).ordenar(None)
        assert False
    except TypeError:
        pass


# ------------------------------------------------------------- C2-6 combate

def test_dano_minimo_uno():
    est = estado_chico()
    est.registrar_sala(sala_simple())
    est.sala_en_curso().enemigos = [EnemigoInstancia("x", "t", 10, 1)]
    r = ataque_jugador(est, "x", 0, 99, None, {})
    assert r.dano == 1 and not r.mato


def test_mata_y_deja_botin():
    est = estado_chico()
    est.registrar_sala(sala_simple())
    est.sala_en_curso().enemigos = [EnemigoInstancia("x", "t", 3, 1)]
    r = ataque_jugador(est, "x", 0, 0, ["moneda"], {})
    assert r.mato and "moneda" in est.sala_en_curso().objetos_suelo


def test_bonus_equipo_suma():
    est = estado_chico()
    est.registrar_sala(sala_simple())
    est.sala_en_curso().enemigos = [EnemigoInstancia("x", "t", 100, 1)]
    arma = SimpleNamespace(clase="arma", ataque_bonus=10)
    sin = ataque_jugador(est, "x", 0, 0, None, {})
    est.jugador.arma_equipada = "espada"
    con = ataque_jugador(est, "x", 0, 0, None, {"espada": arma})
    assert con.dano == sin.dano + 10


def test_enemigo_mata_marca_derrota():
    est = estado_chico()
    est.registrar_sala(sala_simple())
    est.sala_en_curso().enemigos = [EnemigoInstancia("x", "t", 10, 1)]
    est.jugador.vida_actual = 2
    r = ataque_enemigo(est, "x", 50, {})
    assert r.mato and est.estado == "derrota" and est.jugador.vida_actual == 0


def test_atacar_ausente_o_muerto():
    est = estado_chico()
    est.registrar_sala(sala_simple())
    assert "aquí" in ataque_jugador(est, "zz", 1, 0, None, {}).mensaje
    est.sala_en_curso().enemigos = [EnemigoInstancia("x", "t", 0, 1)]
    assert "muerto" in ataque_jugador(est, "x", 1, 0, None, {}).mensaje


# ------------------------------------------------------------- C2-7 efectos

def test_trampa_dana_desarma_y_rearma():
    prov = ProveedorVivo()
    est = EstadoPartida.nueva_partida(prov.general(), "fake-v1")
    est.registrar_sala(prov.sala_lista(1))  # t1-1 pinchos-01 dano 10 rearme 3
    ag, rj = Agenda(), RelojVirtual()
    vida = est.jugador.vida_actual
    res, inv = pisar_trampa(est, ag, rj, "t1-1", prov.catalogo)
    assert res.ok and res.dano == 10 and est.jugador.vida_actual == vida - 10
    assert not est.salas[1].trampas[0].armada and len(res.eventos) == 1
    rj.avanzar(ag)
    assert ejecutar_rearme(est, "t1-1") and est.salas[1].trampas[0].armada


def test_trampa_desarmada_no_dana():
    est = estado_chico()
    s = sala_simple()
    s.trampas = [TrampaInstancia("t", "p", 1, armada=False)]
    est.registrar_sala(s)
    res, _ = pisar_trampa(est, Agenda(), RelojVirtual(), "t", {})
    assert res.ok and res.dano == 0


def test_veneno_ticks_y_antidoto_cancela():
    from src.controller2.efectos import envenenar_legacy
    est = estado_chico()
    est.registrar_sala(sala_simple())
    ag, rj = Agenda(), RelojVirtual()
    envenenar_legacy(est, ag, rj, 3, 2)
    assert est.jugador.efectos["veneno"] == 3
    est.jugador.inventario.append("ant-x")
    res, _ = usar_antidoto(est, ag, "ant-x")
    assert "veneno" not in est.jugador.efectos
    assert all(e.tipo != "veneno" for e in ag) and res.ok


def test_veneno_oficial_80_400():
    est = estado_chico()
    est.registrar_sala(sala_simple())
    ag, rj = Agenda(), RelojVirtual()
    seqs = envenenar(est, ag, rj, 2)
    assert len(seqs) == 5  # 400/80
    assert est.jugador.efectos["veneno"] == 400
    tiempos = sorted(e.t for e in ag)
    assert tiempos == [80, 160, 240, 320, 400]


def test_trampa_venenosa_dana_y_envenena():
    """Mejoras 2026-10: la trampa de la API puede traer `veneno`."""
    prov = ProveedorVivo()
    est = EstadoPartida.nueva_partida(prov.general(), "fake-v1")
    est.registrar_sala(prov.sala_lista(3))  # t3-1 veneno-01: dano 5 + veneno 2
    est.sala_actual = 3
    ag, rj = Agenda(), RelojVirtual()
    vida = est.jugador.vida_actual
    res, inv = pisar_trampa(est, ag, rj, "t3-1", prov.catalogo)
    assert res.ok and res.dano == 5 and "envenenado" in res.mensaje
    assert est.jugador.vida_actual == vida - 5
    assert est.jugador.efectos["veneno"] == 400  # §2.10
    assert len([e for e in ag if e.tipo == "veneno"]) == 5
    assert inv["datos"]["veneno_antes"] is None and inv["eventos"]


def test_trampa_de_llamas_dana_y_quema():
    """Mejoras 2026-10: quemadura propia (3 pulsos 80/240; antídoto no cura)."""
    prov = ProveedorVivo()
    est = EstadoPartida.nueva_partida(prov.general(), "fake-v1")
    est.registrar_sala(prov.sala_lista(1))  # t1-2 llamas-01: dano 3 + quemadura 3
    ag, rj = Agenda(), RelojVirtual()
    vida = est.jugador.vida_actual
    res, inv = pisar_trampa(est, ag, rj, "t1-2", prov.catalogo)
    assert res.ok and res.dano == 3 and "ardiendo" in res.mensaje
    assert est.jugador.vida_actual == vida - 3
    assert est.jugador.efectos["quemadura"] == QUEMADURA_DURACION
    ticks = [e for e in ag if e.tipo == "quemadura"]
    assert len(ticks) == 3 and all(e.datos["dano"] == 3 for e in ticks)
    est.jugador.inventario.append("antidoto-01")
    usar_antidoto(est, ag, "antidoto-01")
    assert "quemadura" in est.jugador.efectos  # el antídoto no la cura


def test_quemadura_ticks_y_apagado():
    est = estado_chico()
    est.registrar_sala(sala_simple())
    ag, rj = Agenda(), RelojVirtual()
    seqs = quemar(est, ag, rj, 3)
    assert len(seqs) == 3  # 240/80 (mejoras 2026-10)
    assert est.jugador.efectos["quemadura"] == QUEMADURA_DURACION
    vida = est.jugador.vida_actual
    assert ejecutar_quemadura(est, 3) and est.jugador.vida_actual == vida - 3
    assert est.jugador.efectos["quemadura"] == 160
    ejecutar_quemadura(est, 3)
    assert not ejecutar_quemadura(est, 3)
    assert "quemadura" not in est.jugador.efectos


def test_deshacer_trampa_restaura_vida_y_efectos():
    """Mejoras 2026-10: deshacer también revierte veneno/quemadura y pulsos."""
    prov = ProveedorVivo()
    est = EstadoPartida.nueva_partida(prov.general(), "fake-v1")
    est.registrar_sala(prov.sala_lista(1))
    ag, rj = Agenda(), RelojVirtual()
    vida = est.jugador.vida_actual
    res, inv = pisar_trampa(est, ag, rj, "t1-2", prov.catalogo)
    assert res.ok and est.jugador.efectos["quemadura"] == QUEMADURA_DURACION
    assert aplicar_inversa(est, ag, inv)
    assert est.jugador.vida_actual == vida
    assert "quemadura" not in est.jugador.efectos
    assert est.salas[1].trampas[1].armada  # t1-2 vuelve a estar armada
    assert all(e.tipo != "quemadura" for e in ag)


def test_pocion_veloz_dura_y_termina():
    prov = ProveedorVivo()
    est = EstadoPartida.nueva_partida(prov.general(), "fake-v1")
    est.registrar_sala(prov.sala_lista(4))
    ag, rj = Agenda(), RelojVirtual()
    est.jugador.inventario.append("pocion-veloz-01")
    res, _ = usar_pocion(est, ag, rj, "pocion-veloz-01", prov.catalogo)
    assert res.ok and est.jugador.efectos["veloz"] == 5
    assert "pocion-veloz-01" not in est.jugador.inventario
    rj.avanzar(ag)
    assert ejecutar_fin_efecto(est, "veloz") and "veloz" not in est.jugador.efectos


def test_antorcha_dura_y_termina():
    prov = ProveedorVivo()
    est = EstadoPartida.nueva_partida(prov.general(), "fake-v1")
    est.registrar_sala(prov.sala_lista(1))
    ag, rj = Agenda(), RelojVirtual()
    est.jugador.inventario.append("antorcha-01")
    res, _ = usar_antorcha(est, ag, rj, "antorcha-01", prov.catalogo)
    # Mejoras 2026-10: la antorcha debe durar lo suficiente para una sala
    # oscura; el valor sale de la ficha (fake: 1200).
    assert res.ok and est.jugador.efectos["antorcha"] == 1200
    assert ejecutar_fin_efecto(est, "antorcha")


# ------------------------------------------------------------- C2-8 enemigos

def _mundo_ia():
    est = estado_chico()
    for n, salidas in ((1, {"E": {"sala": 2}}),
                       (2, {"O": {"sala": 1}, "E": {"sala": 3}}),
                       (3, {"O": {"sala": 2}})):
        est.registrar_sala(sala_simple(n, salidas))
    cat = {"g": SimpleNamespace(comportamiento="guardián", velocidad=5),
           "e": SimpleNamespace(comportamiento="errante", velocidad=5),
           "r": SimpleNamespace(comportamiento="rastreador", velocidad=5)}
    return est, cat


def test_guardian_quieto():
    est, cat = _mundo_ia()
    est.salas[1].enemigos = [EnemigoInstancia("g1", "g", 10, 1)]
    assert decidir_destino(est, "g1", cat, 0) is None


def test_errante_determinista():
    est, cat = _mundo_ia()
    est.salas[2].enemigos = [EnemigoInstancia("e1", "e", 10, 2)]
    assert decidir_destino(est, "e1", cat, 7) == decidir_destino(est, "e1", cat, 7)


def test_rastreador_va_al_rastro():
    est, cat = _mundo_ia()
    est.salas[2].enemigos = [EnemigoInstancia("r1", "r", 10, 2)]
    est.salas[3].ultima_visita = 390  # fresco: ahora 400 - 390 < 400
    assert decidir_destino(est, "r1", cat, 400) == 3
    est.salas[3].ultima_visita = 0  # rancio: 400 - 0 >= 400
    assert decidir_destino(est, "r1", cat, 400) is None


def test_mover_enemigo_cambia_sala():
    est, cat = _mundo_ia()
    est.salas[2].enemigos = [EnemigoInstancia("e1", "e", 10, 2)]
    assert mover_enemigo(est, "e1", 3)
    assert est.salas[2].enemigos == [] and est.salas[3].enemigos[0].sala_actual == 3


def test_turno_reprograma_y_decae_rastro():
    est, cat = _mundo_ia()
    est.salas[1].ultima_visita = 0
    est.salas[2].enemigos = [EnemigoInstancia("e1", "e", 10, 2)]
    ag, rj = Agenda(), RelojVirtual()
    turno_enemigo(est, ag, rj, "e1", cat)
    assert any(e.tipo == "turno" for e in ag)
    # §2.9: rastro es timestamp, no decae por turno.
    assert est.salas[1].ultima_visita == 0


# ------------------------------------------------------------- C2-9 deshacer

def test_pila_tope_cinco():
    pila = PilaDeshacer()
    for i in range(7):
        pila.apilar({"op": "equipar", "datos": {"orden_antes": [i]}, "eventos": []})
    assert len(pila) == 5
    assert pila.desde_lista(pila.a_lista()).a_lista() == pila.a_lista()


def test_seis_acciones_deshacer_cinco():
    est = estado_chico()
    est.registrar_sala(sala_simple())
    est.jugador.inventario = ["pergamino", "a", "b"]
    pila = PilaDeshacer()
    pila.apilar({"op": "equipar", "datos": {"orden_antes": ["pergamino", "a", "b"]},
                 "eventos": []})
    for _ in range(5):
        pila.apilar({"op": "equipar",
                     "datos": {"orden_antes": list(est.jugador.inventario)},
                     "eventos": []})
    ag = Agenda()
    for _ in range(5):
        assert aplicar_inversa(est, ag, pila.desapilar())
    assert est.jugador.inventario == ["pergamino", "a", "b"]


def test_deshacer_combate_restaura_y_quita_botin():
    est = estado_chico()
    est.registrar_sala(sala_simple())
    est.sala_en_curso().enemigos = [EnemigoInstancia("x", "t", 3, 1)]
    r = ataque_jugador(est, "x", 0, 0, ["moneda"], {})
    assert r.mato
    ag = Agenda()
    assert aplicar_inversa(est, ag, {"op": "dano_enemigo",
                                     "datos": {"instancia": "x", "vida_antes": 3,
                                               "botin": ["moneda"]}, "eventos": []})
    assert est.sala_en_curso().enemigos[0].vida_actual == 3
    assert "moneda" not in est.sala_en_curso().objetos_suelo


def test_deshacer_puerta_cancela_cierre():
    est = estado_chico()
    s1 = sala_simple(1, {"E": {"sala": 2, "cerrada": True, "llave": "k",
                              "cierre_automatico": 5}})
    est.registrar_sala(s1)
    ag = Agenda()
    ev = ag.programar(5, "cierre_puerta", {"sala": 1, "direccion": "E"})
    s1.salidas["E"].cerrada = False
    assert aplicar_inversa(est, ag, {"op": "mover",
                                     "datos": {"origen": 1, "abrio": True,
                                               "sala_puerta": 1, "direccion": "E"},
                                     "eventos": [ev.seq]})
    assert s1.salidas["E"].cerrada
    assert all(e.tipo != "cierre_puerta" for e in ag)


def test_deshacer_sin_pergamino_falla():
    est = estado_chico()
    est.registrar_sala(sala_simple())
    pila = PilaDeshacer([{"op": "equipar", "datos": {"orden_antes": []},
                          "eventos": []}])
    ok, msg = deshacer_una(est, Agenda(), pila, {})
    assert not ok and "pergamino" in msg.lower()


def test_deshacer_consume_pergamino():
    est = estado_chico()
    est.registrar_sala(sala_simple())
    est.jugador.inventario = ["pergamino-01", "a"]
    cat = {"pergamino-01": SimpleNamespace(clase="pergamino_retroceso")}
    pila = PilaDeshacer([{"op": "equipar", "datos": {"orden_antes": ["a"]},
                          "eventos": []}])
    ok, _ = deshacer_una(est, Agenda(), pila, cat)
    assert ok and est.jugador.inventario == ["a"] and pila.vacia


# ------------------------------------------------------------- C2-10 victoria

def test_victoria_derrota_y_sin_llave():
    est = estado_chico()  # salida 3, llave "llave-sal"
    est.sala_actual = 3
    assert not hay_victoria(est) and actualizar_estado(est) == "jugando"
    est.jugador.inventario.append("llave-sal")
    # §2.12: tener la llave no basta; hay que haber abierto la puerta de salida.
    assert not hay_victoria(est)
    est.puerta_salida_abierta = True
    assert hay_victoria(est) and actualizar_estado(est) == "victoria"
    est.jugador.vida_actual = 0
    assert hay_derrota(est) and actualizar_estado(est) == "derrota"


def test_puntaje_determinista():
    v = estado_chico()
    assert calcular_puntaje(v, 2) == calcular_puntaje(v, 2)
    assert calcular_puntaje(v, 3) > calcular_puntaje(v, 2)


def test_puntajes_con_mergesort_real():
    assert ordenar_puntajes([30, 10, 20], mergesort) == [10, 20, 30]
    try:
        ordenar_puntajes([2, 1], None)
        assert False
    except TypeError:
        pass


# ------------------------------------------------------------- C2-11 bitacora

def test_linea_formato_y_parseo():
    linea = formatear(12, "mover", "jugador", "E")
    assert linea == "12|mover|jugador|E"
    assert parsear(linea) == {"reloj": 12, "tipo": "mover",
                              "actor": "jugador", "detalle": "E"}


def test_linea_invalida_falla():
    for mala in ["0|volar|jugador|", "solo-dos|campos", "1|mover|a|b|c"]:
        try:
            parsear(mala)
            assert False, mala
        except ValueError:
            pass
    try:
        formatear(0, "volar", "j", "")
        assert False
    except ValueError:
        pass
    try:
        formatear(0, "mover", "j", "a|b")
        assert False
    except ValueError:
        pass


def test_replay_termina_igual():
    prov = ProveedorVivo()

    def nueva():
        est = EstadoPartida.nueva_partida(prov.general(), "fake-v1")
        est.registrar_sala(prov.sala_lista(1))
        return Fachada(est, prov, dict(prov.catalogo))

    a = nueva()
    a.consola(["e"])
    lineas = a.bitacora.leer()
    assert lineas and isinstance(a.bitacora, BitacoraMemoria)
    b = nueva()
    reproducir(b, lineas)
    assert b.estado.sala_actual == a.estado.sala_actual == 2


# ------------------------------------------------------------- C2-12 fachada

def test_consola_solo_fachada_llega_a_victoria():
    fac, _ = fachada_fake()
    # §2.5: abrir y mover separados; victoria exige puerta salida abierta.
    salidas = fac.consola(["s", "recoger llave-hierro-01", "e", "abrir N", "n",
                           "abrir S", "s", "s", "o", "recoger llave-salida-01",
                           "abrir E", "e", "foto"])
    assert fac.estado.estado == "victoria", salidas
    assert len(fac.estado.salas_visitadas) == 6


def test_foto_trae_todo_k5():
    fac, _ = fachada_fake()
    f = fac.foto()
    assert f.sala_id == 1 and f.sala_nombre == "Entrada"
    assert set(f.puertas) >= {"E", "S"}
    assert isinstance(f.objetos_suelo, list) and isinstance(f.trampas, list)
    assert {"vida", "vida_max", "ataque", "defensa", "velocidad", "efectos"} <= set(f.jugador)
    assert f.enemigos and "comportamiento" in f.enemigos[0]
    assert f.inventario == [] and f.equipado is None and f.pergaminos == 0
    assert isinstance(f.mensajes, list) and f.presupuesto == 999
    assert f.estado == "jugando" and f.error is None and f.en_pausa is False


def test_recoger_llena_error_amable():
    est = estado_chico()
    est.inventario_max = 1
    est.registrar_sala(sala_simple())
    est.sala_en_curso().objetos_suelo = ["a", "b"]
    fac = Fachada(est, ProveedorVivo(), {})
    assert fac.recoger("a")[0]
    ok, msg = fac.recoger("b")
    assert not ok and "llena" in msg and fac.foto().error is not None


def test_fachada_deshacer_revierte_recogida():
    fac, _ = fachada_fake()  # sala 1 tiene antorcha-01 en el suelo
    assert fac.recoger("antorcha-01")[0]
    fac.estado.jugador.inventario.append("pergamino-01")
    ok, _ = fac.deshacer()
    assert ok and "antorcha-01" not in fac.estado.jugador.inventario
    assert "antorcha-01" in fac.foto().objetos_suelo
    assert "pergamino-01" not in fac.estado.jugador.inventario  # consumido


def test_fachada_avanzar_ejecuta_cierre():
    est = estado_chico()
    s1 = sala_simple(1, {"E": {"sala": 2, "cerrada": True, "llave": "k",
                              "cierre_automatico": 5}})
    est.registrar_sala(sala_simple(2))
    est.registrar_sala(s1)
    est.jugador.inventario.append("k")

    class Prov2:
        def sala_lista(self, n):
            return sala_simple(n)

    fac = Fachada(est, Prov2(), {})
    assert fac.abrir("E")[0]
    assert fac.mover("E")[0]
    assert fac.avanzar() == "cierre_puerta"
    assert s1.salidas["E"].cerrada


def test_fachada_atacar_y_botín_fake():
    fac, prov = fachada_fake()  # e1-1 esqueleto guardian vida 40, suelta pocion-roja-01
    vidas = []
    for _ in range(10):
        ok, _ = fac.atacar("e1-1")
        vidas.append(fac.estado.salas[1].enemigos[0].vida_actual)
        if "pocion-roja-01" in fac.foto().objetos_suelo:
            break
    assert "pocion-roja-01" in fac.foto().objetos_suelo
    assert vidas[0] < 40


# ------------------------------------------------------------- revisita sin respawn
def test_reentrar_no_duplica_objetos():
    fac, _ = fachada_fake()  # sala 1: antorcha-01 en el suelo
    assert fac.recoger('antorcha-01')[0]
    assert 'antorcha-01' not in fac.foto().objetos_suelo
    assert fac.mover('E')[0] and fac.mover('O')[0]  # 1->2->1
    assert fac.foto().sala_id == 1
    assert 'antorcha-01' not in fac.foto().objetos_suelo
    assert 'antorcha-01' in fac.estado.jugador.inventario


def test_reentrar_no_revive_enemigos_ni_rearma():
    fac, prov = fachada_fake()
    sala1 = fac.estado.salas[1]
    for _ in range(30):  # mata a e1-1 (vida 40)
        fac.atacar('e1-1')
        if not sala1.enemigos[0].vivo:
            break
    assert not sala1.enemigos[0].vivo
    trampa = sala1.trampas[0].instancia
    fac.pisar_trampa(trampa)
    assert not fac.estado.salas[1].trampas[0].armada
    assert fac.mover('E')[0] and fac.mover('O')[0]
    de_vuelta = fac.estado.salas[1]
    assert not de_vuelta.enemigos[0].vivo
    assert not de_vuelta.trampas[0].armada


def test_revisita_no_pide_al_proveedor():
    from src.controller2 import intentar_mover
    from src.controller2 import Agenda, RelojVirtual
    llamadas = []

    class Contador:
        def sala_lista(self, n):
            llamadas.append(n)
            return ProveedorVivo().sala_lista(n)

    prov = ProveedorVivo()
    est = EstadoPartida.nueva_partida(prov.general(), 'fake-v1')
    est.registrar_sala(prov.sala_lista(1))
    ag, rj = Agenda(), RelojVirtual()
    assert intentar_mover(est, 'E', Contador(), ag, rj).ok  # 1->2 pide
    assert intentar_mover(est, 'O', Contador(), ag, rj).ok  # 2->1 viva: no pide
    assert intentar_mover(est, 'E', Contador(), ag, rj).ok  # 1->2 viva: no pide
    assert llamadas == [2]


# ------------------------------------------------------------- oleadas C2-8
def _fachada_oleada(cada=100, semilla=9):
    from src.controller2 import Fachada
    prov = ProveedorVivo()
    est = EstadoPartida.nueva_partida(prov.general(), 'fake-v1')
    est.registrar_sala(prov.sala_lista(1))
    return Fachada(est, prov, dict(prov.catalogo), semilla=semilla,
                   oleada_cada=cada), prov


def _avanzar_hasta(fac, cond, tope=25):
    for _ in range(tope):
        if cond():
            return True
        fac.avanzar()
    return cond()


def _oleadas_vivas(fac):
    return [e for s in fac.estado.salas.values() for e in s.enemigos
            if e.instancia.startswith('oleada-') and e.vivo]


def test_oleada_aparece_errante_y_ataca():
    fac, _ = _fachada_oleada()
    assert _avanzar_hasta(fac, lambda: len(_oleadas_vivas(fac)) > 0)
    esp = _oleadas_vivas(fac)[0]
    assert esp.activa and esp.sala_actual == 1  # aparece donde estas
    assert esp.tipo_id == 'murcielago-errante-01'  # pool errante del catalogo
    vida = fac.estado.jugador.vida_actual
    assert _avanzar_hasta(fac, lambda: fac.estado.jugador.vida_actual < vida)
    assert fac.estado.salas[1].enemigos  # sigue ahi tras atacar


def test_oleada_respeta_tope_y_reprograma():
    from src.controller2 import EnemigoInstancia
    fac, _ = _fachada_oleada()
    sala1 = fac.estado.salas[1]
    for i in range(4):
        sala1.enemigos.append(EnemigoInstancia(f'oleada-x{i}', 'murcielago-errante-01', 20, 1))
    assert _avanzar_hasta(fac, lambda: not any(e.tipo == 'oleada' and e.t <= fac.reloj.ahora for e in fac.agenda))
    assert len(_oleadas_vivas(fac)) == 4  # tope: no aparece el quinto
    assert any(e.tipo == 'oleada' for e in fac.agenda)  # pero se reprograma


def test_oleada_deshacer_la_retira():
    fac, _ = _fachada_oleada()
    assert _avanzar_hasta(fac, lambda: len(_oleadas_vivas(fac)) > 0)
    inst = _oleadas_vivas(fac)[0].instancia
    fac.estado.jugador.inventario.append('pergamino-01')
    ok, _ = fac.deshacer()
    assert ok
    assert inst not in [e.instancia for s in fac.estado.salas.values() for e in s.enemigos]
    assert not any((e.datos or {}).get('actor') == inst for e in fac.agenda)


def test_oleada_determinista_misma_semilla():
    fa, _ = _fachada_oleada()
    fb, _ = _fachada_oleada()
    for _ in range(8):
        fa.avanzar()
        fb.avanzar()
    a = sorted((e.instancia, e.tipo_id) for e in _oleadas_vivas(fa))
    b = sorted((e.instancia, e.tipo_id) for e in _oleadas_vivas(fb))
    assert a and a == b


def test_oleada_sobrevive_guardado():
    fac, _ = _fachada_oleada()
    assert _avanzar_hasta(fac, lambda: len(_oleadas_vivas(fac)) > 0)
    from src.controller2 import Fachada
    data = fac.guardar()
    prov = ProveedorVivo()
    fac2 = Fachada(EstadoPartida.desde_dict(data), prov, dict(prov.catalogo))
    assert len([e for s in fac2.estado.salas.values() for e in s.enemigos
                if e.instancia.startswith('oleada-')]) == len(_oleadas_vivas(fac))


def test_errante_se_mueve_random():
    from src.controller2 import turno_enemigo, Agenda, RelojVirtual
    from src.controller2.azar import Azar
    est = estado_chico()
    for n, salidas in ((1, {'E': {'sala': 2}}),
                       (2, {'O': {'sala': 1}, 'E': {'sala': 3}}),
                       (3, {'O': {'sala': 2}})):
        est.registrar_sala(sala_simple(n, salidas))
    est.sala_actual = 1
    est.salas[2].enemigos = [EnemigoInstancia('e1', 'murcielago-errante-01', 20, 2)]
    cat = {'murcielago-errante-01': ProveedorVivo().catalogo['murcielago-errante-01']}
    ag, rj, azar = Agenda(), RelojVirtual(), Azar(7)
    posiciones = []
    for _ in range(10):
        turno_enemigo(est, ag, rj, 'e1', cat, azar=azar)
        posiciones.append(next(e.sala_actual for s in est.salas.values()
                               for e in s.enemigos if e.instancia == 'e1'))
    assert len(set(posiciones)) > 1  # vago entre salas, no quieto
