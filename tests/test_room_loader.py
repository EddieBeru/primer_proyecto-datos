"""C1-7: cargador arma SalaLista (lote vecinos + fichas + suelta), sin red."""

import pytest

from src.controller1.budget import BudgetAdapter
from src.controller1.lru_cache import CacheLRU
from src.controller1.room_loader import RoomLoader
from src.controller1 import endpoints
from src.models.catalog import Enemy, Trap
from src.models.errors import NotFoundError, UnexpectedResponseError
from src.models.objects import Antidote
from src.models.roomContents import ContenidoResponse, EnemyPlacement, RoomContentEntry, TrapPlacement
from src.models.rooms import Exit, Room


FICHAS = {
    "goblin": Enemy(id="goblin", nombre="Goblin", vida_max=30, ataque=6,
                    defensa=2, velocidad=7, comportamiento="guardián",
                    suelta=["pocion-test"]),
    "pinchos": Trap(id="pinchos", nombre="Pinchos", dano=10, rearme=3),
    "pocion-test": Antidote(id="pocion-test", nombre="Poción", peso=1, valor=5),
}

PLANO = {
    1: Room(id=1, nombre="A", salidas={"E": Exit(sala=2), "S": Exit(sala=3)}),
    2: Room(id=2, nombre="B", salidas={"O": Exit(sala=1)}),
    3: Room(id=3, nombre="C", salidas={"N": Exit(sala=1)}),
}

CONTENIDO = {
    1: RoomContentEntry(sala=1,
                        enemigos=[EnemyPlacement(instancia="e1", tipo="goblin", vida=None)],
                        objetos=["pocion-test"],
                        trampas=[TrapPlacement(instancia="t1", tipo="pinchos")]),
    2: RoomContentEntry(sala=2, enemigos=[], objetos=[], trampas=[]),
    3: RoomContentEntry(sala=3, enemigos=[], objetos=[], trampas=[]),
}


def _mockear(monkeypatch, llamadas):
    def fake_contenido(cripta_id, salas, budget=None):
        llamadas.setdefault("contenido", []).append((cripta_id, list(salas), budget))
        return ContenidoResponse(contenido=[CONTENIDO[s] for s in salas])

    def fake_lote(ids, budget=None):
        llamadas.setdefault("lotes", []).append((list(ids), budget))
        return {i: FICHAS[i] for i in ids}

    monkeypatch.setattr(endpoints, "contenido", fake_contenido)
    monkeypatch.setattr(endpoints, "lote_catalogo_auto", fake_lote)


def test_pide_vecinas_en_un_lote_y_reutiliza(monkeypatch):
    llamadas = {}
    _mockear(monkeypatch, llamadas)
    loader = RoomLoader("c1", PLANO)

    sala = loader.sala_lista(1)
    assert llamadas["contenido"] == [("c1", [1, 2, 3], None)]
    assert sala.room.nombre == "A"
    assert [(e.instancia, e.ficha.id, e.vida_actual) for e in sala.enemigos] == [("e1", "goblin", 30)]
    assert [o.ficha.id for o in sala.objetos] == ["pocion-test"]
    assert [(t.instancia, t.ficha.id) for t in sala.trampas] == [("t1", "pinchos")]

    loader.sala_lista(2)  # contenido ya guardado: sin nueva petición
    assert len(llamadas["contenido"]) == 1


def test_suelta_se_precarga(monkeypatch):
    llamadas = {}
    _mockear(monkeypatch, llamadas)
    sala = RoomLoader("c1", PLANO).sala_lista(1)
    fases = [ids for ids, _ in llamadas["lotes"]]
    # suelta (pocion-test) ya vino en fase 1 como objeto de suelo: sin refetch
    assert fases == [["goblin", "pinchos", "pocion-test"]]
    assert sala.enemigos[0].ficha.suelta == ["pocion-test"]


def test_suelta_no_en_suelo_se_pide_en_fase2(monkeypatch):
    llamadas = {}
    _mockear(monkeypatch, llamadas)
    CONTENIDO[2].enemigos = [EnemyPlacement(instancia="e2", tipo="goblin", vida=None)]
    try:
        RoomLoader("c1", PLANO).sala_lista(2)
        fases = [ids for ids, _ in llamadas["lotes"]]
        assert fases[0] == ["goblin"]
        assert fases[1] == ["pocion-test"]  # suelta no estaba en sala: se trae aparte
    finally:
        CONTENIDO[2].enemigos = []


def test_sala_inexistente_404_sin_pedir(monkeypatch):
    llamadas = {}
    _mockear(monkeypatch, llamadas)
    with pytest.raises(NotFoundError):
        RoomLoader("c1", PLANO).sala_lista(99)
    assert llamadas == {}


def test_cache_evita_repedir(monkeypatch):
    llamadas = {}
    _mockear(monkeypatch, llamadas)
    cache = CacheLRU(capacidad=10)
    cache.guardar("goblin", FICHAS["goblin"])
    RoomLoader("c1", PLANO, cache=cache).sala_lista(1)
    fases = [ids for ids, _ in llamadas["lotes"]]
    assert fases[0] == ["pinchos", "pocion-test"]  # goblin vino de caché


def test_budget_se_pasa(monkeypatch):
    llamadas = {}
    _mockear(monkeypatch, llamadas)
    budget = BudgetAdapter(presupuesto=9)
    RoomLoader("c1", PLANO, budget=budget).sala_lista(1)
    assert llamadas["contenido"][0][2] is budget
    assert all(b is budget for _, b in llamadas["lotes"])


def test_vida_explicita_se_respeta(monkeypatch):
    llamadas = {}
    _mockear(monkeypatch, llamadas)
    CONTENIDO[1].enemigos = [EnemyPlacement(instancia="e1", tipo="goblin", vida=12)]
    try:
        sala = RoomLoader("c1", PLANO).sala_lista(1)
        assert sala.enemigos[0].vida_actual == 12
    finally:
        CONTENIDO[1].enemigos = [EnemyPlacement(instancia="e1", tipo="goblin", vida=None)]


def test_tipo_no_enemigo_error_propio(monkeypatch):
    llamadas = {}
    _mockear(monkeypatch, llamadas)
    CONTENIDO[2].enemigos = [EnemyPlacement(instancia="ex", tipo="pinchos", vida=None)]
    try:
        with pytest.raises(UnexpectedResponseError):
            RoomLoader("c1", PLANO).sala_lista(2)
    finally:
        CONTENIDO[2].enemigos = []
