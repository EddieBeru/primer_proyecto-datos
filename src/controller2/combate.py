
from __future__ import annotations

from dataclasses import dataclass, field


def calcular_dano(ataque_total: int, defensa_total: int, azar=None) -> int:
    """§2.6: max(1, atk + randint(0,4) - defensa). Sin azar -> 0 extra (tests)."""
    extra = 0
    if azar is not None:
        extra = int(azar.randint(0, 4))
        try:
            from src.controller2.modelo import EstadoPartida  # noqa: F401
        except Exception:
            pass
    return max(1, int(ataque_total) + int(extra) - int(defensa_total))


def bonus_arma(catalogo: dict, arma_id: str | None) -> int:
    # TODO(C1-6/C1-7): la ficha debe venir de la cache LRU o del lote de 10; si falta, C1 la precarga.
    if not arma_id:
        return 0
    ficha = catalogo.get(arma_id)
    return int(getattr(ficha, "ataque_bonus", 0) or 0)


def bonus_armadura(catalogo: dict, armadura_id: str | None) -> int:
    # TODO(C1-6/C1-7): igual que bonus_arma pero con defensa_bonus.
    if not armadura_id:
        return 0
    ficha = catalogo.get(armadura_id)
    return int(getattr(ficha, "defensa_bonus", 0) or 0)


@dataclass
class ResultadoAtaque:
    dano: int
    vida_restante_objetivo: int
    mato: bool
    botin: list[str] = field(default_factory=list)
    mensaje: str = ""


def ataque_jugador(
    estado,
    instancia_id: str,
    ataque_enemigo: int,
    defensa_enemigo: int,
    suelta: list[str] | None,
    catalogo: dict | None = None,
    azar=None,
    agenda=None,
) -> ResultadoAtaque:
    """El jugador pega al enemigo de la sala actual. Lo mata si vida llega a 0."""
    if not estado.jugador.vivo:
        return ResultadoAtaque(0, 0, False, [], "El jugador está muerto.")
    sala = estado.salas.get(estado.sala_actual)
    if sala is None:
        return ResultadoAtaque(0, 0, False, [], "Sala desconocida.")
    objetivo = next((e for e in sala.enemigos if e.instancia == instancia_id), None)
    if objetivo is None:
        return ResultadoAtaque(0, 0, False, [], "Ese enemigo no está aquí.")
    if not objetivo.vivo:
        return ResultadoAtaque(0, 0, False, [], "Ya estaba muerto.")
    atk = estado.jugador.ataque_total(bonus_arma(catalogo or {}, estado.jugador.arma_equipada))
    dano = calcular_dano(atk, defensa_enemigo, azar)
    if azar is not None:
        try:
            estado.azar_llamadas = int(getattr(estado, "azar_llamadas", 0)) + 1
        except Exception:
            pass
    objetivo.recibir_dano(dano)
    botin: list[str] = []
    if not objetivo.vivo:
        botin = list(suelta or [])
        sala.objetos_suelo.extend(botin)
        try:
            estado.enemigos_derrotados = int(getattr(estado, "enemigos_derrotados", 0)) + 1
        except Exception:
            pass
        if agenda is not None:
            try:
                agenda.cancelar_donde(
                    lambda e: e.tipo == "turno" and (e.datos or {}).get("actor") == instancia_id
                )
            except Exception:
                pass
    return ResultadoAtaque(dano, objetivo.vida_actual, not objetivo.vivo, botin)


def ataque_enemigo(
    estado,
    instancia_id: str,
    ataque_enemigo: int,
    catalogo: dict | None = None,
    azar=None,
) -> ResultadoAtaque:
    """Un enemigo vivo pega al jugador. Marca derrota si vida llega a 0."""
    sala = estado.salas.get(estado.sala_actual)
    if sala is None:
        return ResultadoAtaque(0, estado.jugador.vida_actual, False, [], "Sala desconocida.")
    agresor = next((e for e in sala.enemigos if e.instancia == instancia_id), None)
    if agresor is None or not agresor.vivo:
        return ResultadoAtaque(0, estado.jugador.vida_actual, False, [], "Ese enemigo no ataca.")
    defensa = estado.jugador.defensa_total(
        bonus_armadura(catalogo or {}, estado.jugador.armadura_equipada)
    )
    dano = calcular_dano(ataque_enemigo, defensa, azar)
    if azar is not None:
        try:
            estado.azar_llamadas = int(getattr(estado, "azar_llamadas", 0)) + 1
        except Exception:
            pass
    estado.jugador.recibir_dano(dano)
    murio = not estado.jugador.vivo
    if murio:
        estado.estado = "derrota"
    return ResultadoAtaque(dano, estado.jugador.vida_actual, murio)
