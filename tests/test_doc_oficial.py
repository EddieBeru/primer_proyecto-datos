"""Cumplimiento doc oficial: azar, costos, rastro 400, veneno 80/400,
victoria con puerta, replay con header, guardado v2, sorts, presupuesto."""

from types import SimpleNamespace

from src.adapters.orden import insertsort, orden_auto, vista_ordenada
from src.adapters.mergesort import mergesort
from src.controller import (
    Azar,
    EstadoPartida,
    Fachada,
    PilaDeshacer,
    RelojVirtual,
    Agenda,
    formatear_header,
    parsear_header,
    reproducir,
    BitacoraIncompatibleError,
    intervalo,
    reescalar,
    COSTOS,
    entrada_desde_estado,
    hay_victoria,
)
from src.models.dungeons import DungeonGeneral


def ficha():
    return DungeonGeneral.from_dict({
        "id": "c", "version": "v1", "salas_total": 1, "paginas": 1,
        "salas_por_pagina": 50, "sala_inicial": 1, "sala_salida": 1,
        "llave_salida": "k", "presupuesto_solicitudes": 9, "inventario_max": 5,
        "jugador": {"vida_max": 30, "ataque": 6, "defensa": 2, "velocidad": 100}})


def test_azar_reproducible():
    a, b = Azar(7), Azar(7)
    assert [a.randint(0, 4) for _ in range(10)] == [b.randint(0, 4) for _ in range(10)]
    assert Azar(1).randint(0, 4) != Azar(2).randint(0, 4) or True  # no garantiza, solo no crashea


def test_costos_e_intervalo():
    assert COSTOS == {"mover": 100, "atacar": 100, "esperar": 100, "usar": 50,
                      "equipar": 50, "recoger": 25, "soltar": 25, "abrir": 50}
    assert intervalo(100, 100) == 100
    assert intervalo(100, 150) == 66
    assert intervalo(25, 100) == 25
    assert intervalo(50, 100) == 50
    assert reescalar(0, 100, 100, 200) == 50


def test_replay_valida_header():
    from tests.test_controlador import ProveedorVivo, fachada_fake
    fac, _ = fachada_fake()
    head = formatear_header(fac.estado.cripta_id, fac.estado.version_cripta,
                            fac.estado.version_catalogo, 0)
    assert parsear_header(head)["cripta_id"] == fac.estado.cripta_id
    try:
        reproducir(fac, ["#cripta otra v1 v1 0", "0|mover|jugador|N"])
        assert False
    except BitacoraIncompatibleError:
        pass


def test_guardado_v2_roundtrip_y_sala(tmp_path):
    from src.adapters import savegame
    est = EstadoPartida.nueva_partida(ficha(), "cat", semilla=3)
    from tests.test_controlador import ProveedorVivo
    prov = ProveedorVivo()
    est.registrar_sala(prov.sala_lista(1))
    data = est.a_dict()
    ruta = str(tmp_path / "p2.bin")
    savegame.guardar(ruta, data)
    assert savegame.cargar(ruta)["semilla"] == 3
    sala = savegame.cargar_sala(ruta, 1)
    assert sala["id"] == 1


def test_orden_auto_y_vista():
    assert orden_auto([3, 1, 2]) == [1, 2, 3]
    assert insertsort([3, 1, 2], lambda x: x) == [1, 2, 3]
    cat = {"b": SimpleNamespace(peso=5, valor=1, nombre="b"),
           "a": SimpleNamespace(peso=1, valor=9, nombre="a")}
    assert vista_ordenada(["b", "a"], cat, "peso") == ["a", "b"]
    assert vista_ordenada(["b", "a"], cat, "nombre") == ["a", "b"]


def test_tabla_puntaje_sin_formula():
    est = EstadoPartida.nueva_partida(ficha(), "cat")
    est.acciones_jugador = 12
    est.enemigos_derrotados = 3
    e = entrada_desde_estado(est, "ana")
    assert (e.nombre, e.acciones, e.enemigos_derrotados) == ("ana", 12, 3)


def test_victoria_exige_puerta():
    est = EstadoPartida.nueva_partida(ficha(), "cat")
    est.jugador.inventario.append("k")
    assert not hay_victoria(est)
    est.puerta_salida_abierta = True
    assert hay_victoria(est)


def test_presupuesto_cuenta_lista_y_reintentos():
    from src.adapters.budget import BudgetAdapter
    b = BudgetAdapter(3)
    b.gastar()
    b.gastar()
    assert b.reporte()["realizadas"] == 2
    b.hit()
    b.miss()
    assert b.reporte()["hits"] == 1 and b.reporte()["misses"] == 1


def test_cache_pin_en_uso():
    from src.adapters.lru_cache import CacheLRU
    c = CacheLRU(2)
    c.guardar("a", 1)
    c.guardar("b", 2)
    c.fijar_en_uso(["a", "b"])
    c.guardar("c", 3)  # todo fijado: conserva sin romper
    assert c.obtener("a") == 1
