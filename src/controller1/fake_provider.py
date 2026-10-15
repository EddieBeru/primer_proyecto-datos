from dataclasses import dataclass, field

from src.models.catalog import Enemy, Trap
from src.models.dungeons import CriptasResponse, DungeonGeneral, DungeonSummary, PlayerInitial
from src.models.errors import NotFoundError
from src.models.objects import (
    Antidote,
    Armor,
    Key,
    Potion,
    RewindScroll,
    Torch,
    Weapon,
)
from src.models.roomContents import EnemyPlacement, RoomContentEntry, TrapPlacement
from src.models.rooms import Exit, Room
from src.models.types import Entidad

CRIPTA_ID = "cripta-ejemplo"
PRESUPUESTO_FAKE = 999


# ---------------------------------------------------------------- fichas fijas
def _fichas_fijas() -> dict[str, Entidad]:
    return {
        # enemigos (3 comportamientos)
        "esqueleto-guardian-01": Enemy(
            id="esqueleto-guardian-01",
            nombre="Esqueleto guardián",
            vida_max=40,
            ataque=8,
            defensa=3,
            velocidad=5,
            comportamiento="guardián",
            suelta=["pocion-roja-01"],
        ),
        "murcielago-errante-01": Enemy(
            id="murcielago-errante-01",
            nombre="Murciélago errante",
            vida_max=20,
            ataque=5,
            defensa=1,
            velocidad=12,
            comportamiento="errante",
            suelta=[],
        ),
        "sombra-rastreadora-01": Enemy(
            id="sombra-rastreadora-01",
            nombre="Sombra rastreadora",
            vida_max=30,
            ataque=7,
            defensa=2,
            velocidad=8,
            comportamiento="rastreador",
            suelta=["antorcha-01"],
        ),
        "jefe-cripta-01": Enemy(
            id="jefe-cripta-01",
            nombre="Señor de la cripta",
            vida_max=80,
            ataque=14,
            defensa=6,
            velocidad=6,
            comportamiento="guardián",
            suelta=["pocion-roja-01", "antorcha-01"],
        ),
        # equipo / consumibles
        "espada-hierro-01": Weapon(
            id="espada-hierro-01", nombre="Espada de hierro",
            peso=3, valor=50, ataque_bonus=4,
        ),
        "escudo-madera-01": Armor(
            id="escudo-madera-01", nombre="Escudo de madera",
            peso=4, valor=30, defensa_bonus=3,
        ),
        "pocion-roja-01": Potion(
            id="pocion-roja-01", nombre="Poción roja",
            peso=1, valor=20, cura=25,
            modificador_velocidad=None, duracion=None,
        ),
        "pocion-veloz-01": Potion(
            id="pocion-veloz-01", nombre="Poción veloz",
            peso=1, valor=35, cura=None,
            modificador_velocidad=4, duracion=5,
        ),
        "antidoto-01": Antidote(
            id="antidoto-01", nombre="Antídoto",
            peso=1, valor=15,
        ),
        "llave-hierro-01": Key(
            id="llave-hierro-01", nombre="Llave de hierro",
            peso=1, valor=5, abre="sala-4",
        ),
        "llave-salida-01": Key(
            id="llave-salida-01", nombre="Llave de salida",
            peso=1, valor=100, abre="sala-6",
        ),
        "antorcha-01": Torch(
            id="antorcha-01", nombre="Antorcha",
            peso=2, valor=10, duracion=10,
        ),
        "pergamino-01": RewindScroll(
            id="pergamino-01", nombre="Pergamino de retroceso",
            peso=1, valor=40,
        ),
        # trampa
        "pinchos-01": Trap(
            id="pinchos-01", nombre="Pinchos",
            dano=10, rearme=3,
        ),
        "veneno-01": Trap(
            id="veneno-01", nombre="Dardo envenenado",
            dano=5, rearme=None,
        ),
    }


def _ficha_general() -> DungeonGeneral:
    return DungeonGeneral(
        id=CRIPTA_ID,
        version="fake-v1",
        salas_total=6,
        paginas=1,
        salas_por_pagina=50,
        sala_inicial=1,
        sala_salida=6,
        llave_salida="llave-salida-01",
        presupuesto_solicitudes=PRESUPUESTO_FAKE,
        inventario_max=10,
        jugador=PlayerInitial(vida_max=100, ataque=10, defensa=5, velocidad=10),
    )


def _esqueleto() -> dict[int, Room]:
    # Mapa cerrado 6 salas. Ruta crítica 1->3->4->5->6.
    # 2->4 y 5->6 cerradas con llave. 4->6 con cierre automático.
    return {
        1: Room(id=1, nombre="Entrada", salidas={
            "E": Exit(sala=2),
            "S": Exit(sala=3),
        }),
        2: Room(id=2, nombre="Armería", salidas={
            "O": Exit(sala=1),
            "S": Exit(sala=4, cerrada=True, llave="llave-hierro-01"),
        }),
        3: Room(id=3, nombre="Capilla oscura", salidas={
            "N": Exit(sala=1),
            "E": Exit(sala=4),
            "S": Exit(sala=5),
        }),
        4: Room(id=4, nombre="Pasillo húmedo", salidas={
            "N": Exit(sala=2, cerrada=True, llave="llave-hierro-01"),
            "O": Exit(sala=3),
            "S": Exit(sala=6, cierre_automatico=3),
        }),
        5: Room(id=5, nombre="Osario", salidas={
            "N": Exit(sala=3),
            "E": Exit(sala=6, cerrada=True, llave="llave-salida-01"),
        }),
        6: Room(id=6, nombre="Salida", salidas={
            "O": Exit(sala=5),
            "N": Exit(sala=4),
        }),
    }


def _contenido() -> dict[int, RoomContentEntry]:
    return {
        1: RoomContentEntry(
            sala=1,
            enemigos=[EnemyPlacement(instancia="e1-1", tipo="esqueleto-guardian-01", vida=None)],
            objetos=["antorcha-01"],
            trampas=[TrapPlacement(instancia="t1-1", tipo="pinchos-01")],
        ),
        2: RoomContentEntry(
            sala=2,
            enemigos=[EnemyPlacement(instancia="e2-1", tipo="murcielago-errante-01", vida=20)],
            objetos=["espada-hierro-01", "escudo-madera-01"],
            trampas=[],
        ),
        3: RoomContentEntry(
            sala=3,
            enemigos=[EnemyPlacement(instancia="e3-1", tipo="sombra-rastreadora-01", vida=None)],
            objetos=["llave-hierro-01", "pocion-roja-01"],
            trampas=[TrapPlacement(instancia="t3-1", tipo="veneno-01")],
        ),
        4: RoomContentEntry(
            sala=4,
            enemigos=[EnemyPlacement(instancia="e4-1", tipo="esqueleto-guardian-01", vida=40)],
            objetos=["antidoto-01", "pocion-veloz-01"],
            trampas=[TrapPlacement(instancia="t4-1", tipo="pinchos-01")],
        ),
        5: RoomContentEntry(
            sala=5,
            enemigos=[
                EnemyPlacement(instancia="e5-1", tipo="murcielago-errante-01", vida=None),
                EnemyPlacement(instancia="e5-2", tipo="sombra-rastreadora-01", vida=30),
            ],
            objetos=["llave-salida-01", "pergamino-01"],
            trampas=[],
        ),
        6: RoomContentEntry(
            sala=6,
            enemigos=[EnemyPlacement(instancia="e6-1", tipo="jefe-cripta-01", vida=None)],
            objetos=[],
            trampas=[],
        ),
    }


# ------------------------------------------------------- sala lista (Flujo C)
@dataclass
class EnemigoListo:
    instancia: str
    ficha: Enemy
    vida_actual: int  # vida colocación si viene, si no vida_max del tipo


@dataclass
class TrampaLista:
    instancia: str
    ficha: Trap
    armada: bool = True


@dataclass
class ObjetoListo:
    ficha: Entidad


@dataclass
class SalaLista:
    room: Room
    enemigos: list[EnemigoListo] = field(default_factory=list)
    objetos: list[ObjetoListo] = field(default_factory=list)
    trampas: list[TrampaLista] = field(default_factory=list)


class FakeProvider:
    """Proveedor K1 falso. Constructor sin args, sin red."""

    def __init__(self) -> None:
        self._fichas = _fichas_fijas()
        self._salas = _esqueleto()
        self._contenido = _contenido()
        self._general = _ficha_general()
        self._preparada: str | None = None
        self._presupuesto = PRESUPUESTO_FAKE

    # K1: lista criptas (endpoint 1)
    def listar_criptas(self) -> CriptasResponse:
        return CriptasResponse(criptas=[
            DungeonSummary(id=CRIPTA_ID, nombre="Cripta ejemplo", salas=6, dificultad=1),
        ])

    # K1: preparar cripta (endpoints 2+4). Deja esqueleto listo.
    def preparar_cripta(self, cripta_id: str) -> DungeonGeneral:
        if cripta_id != CRIPTA_ID:
            raise NotFoundError(f"cripta inexistente: {cripta_id}")
        self._preparada = cripta_id
        return self._general

    # K1: sala N lista (Flujo C ya resuelto: sin ids, con fichas)
    def sala_lista(self, n: int) -> SalaLista:
        room = self._salas.get(n)
        entry = self._contenido.get(n)
        if room is None or entry is None:
            raise NotFoundError(f"sala inexistente: {n}")
        enemigos = [
            EnemigoListo(
                instancia=e.instancia,
                ficha=self._ficha_obligatoria(e.tipo),
                vida_actual=e.vida if e.vida is not None else self._vida_max(e.tipo),
            )
            for e in entry.enemigos
        ]
        objetos = [ObjetoListo(ficha=self._ficha_obligatoria(oid)) for oid in entry.objetos]
        # precarga suelta como haría C1-7 real: valida que existen
        for e in enemigos:
            for drop in (e.ficha.suelta or []):
                self._ficha_obligatoria(drop)
        trampas = [
            TrampaLista(instancia=t.instancia, ficha=self._ficha_obligatoria(t.tipo))
            for t in entry.trampas
        ]
        return SalaLista(room=room, enemigos=enemigos, objetos=objetos, trampas=trampas)

    # K1: ficha suelta (caché primero en real; aquí dict directo)
    def ficha(self, entidad_id: str) -> Entidad:
        try:
            return self._fichas[entidad_id]
        except KeyError:
            raise NotFoundError(f"ficha inexistente: {entidad_id}") from None

    # K1: presupuesto restante
    def presupuesto_restante(self) -> int:
        return self._presupuesto

    def _ficha_obligatoria(self, entidad_id: str) -> Entidad:
        try:
            return self._fichas[entidad_id]
        except KeyError:
            raise NotFoundError(f"ficha inexistente: {entidad_id}") from None

    def _vida_max(self, tipo_id: str) -> int:
        ficha = self._ficha_obligatoria(tipo_id)
        if isinstance(ficha, Enemy):
            return ficha.vida_max
        raise NotFoundError(f"tipo {tipo_id} no es enemigo")


# Singleton + funciones módulo: C2 importa el módulo, luego cambia a real sin tocar llamadas.
_default = FakeProvider()


def listar_criptas() -> CriptasResponse:
    return _default.listar_criptas()


def preparar_cripta(cripta_id: str) -> DungeonGeneral:
    return _default.preparar_cripta(cripta_id)


def sala_lista(n: int) -> SalaLista:
    return _default.sala_lista(n)


def ficha(entidad_id: str) -> Entidad:
    return _default.ficha(entidad_id)


def presupuesto_restante() -> int:
    return _default.presupuesto_restante()
