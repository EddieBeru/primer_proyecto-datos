
from __future__ import annotations

from dataclasses import dataclass, field


def calcular_dano(ataque_total: int, defensa_total: int) -> int:
    # TODO(profe pregunta 5): reemplazar por la formula real del enunciado; solo cambiar aqui.
    return max(1, int(ataque_total) - int(defensa_total))


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
) -> ResultadoAtaque:
    """El jugador pega al enemigo de la sala actual. Lo mata si vida llega a 0."""
    # TODO(C1-7): `suelta` ya viene precargada en la sala lista; si apunta a id nunca visto, C1 lo pide en lote.
    # TODO(C2-2): al morir, cancelar sus turnos pendientes en la agenda para que no actue muerto.
    # TODO(C2-9): guardar vida anterior + botin puesto en suelo como accion inversa.
    # TODO(C2-11): anotar ataque/muerte/botin a bitacora (K3).
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
    dano = calcular_dano(atk, defensa_enemigo)
    objetivo.recibir_dano(dano)
    botin: list[str] = []
    if not objetivo.vivo:
        botin = list(suelta or [])
        sala.objetos_suelo.extend(botin)
    return ResultadoAtaque(dano, objetivo.vida_actual, not objetivo.vivo, botin)


def ataque_enemigo(
    estado,
    instancia_id: str,
    ataque_enemigo: int,
    catalogo: dict | None = None,
) -> ResultadoAtaque:
    """Un enemigo vivo pega al jugador. Marca derrota si vida llega a 0."""
    # TODO(C2-10): la derrota aqui es parcial; fin-de-juego define puntaje y pantalla (C2-12).
    # TODO(C2-9): guardar vida anterior del jugador como inversa (deshacer tras combate).
    sala = estado.salas.get(estado.sala_actual)
    if sala is None:
        return ResultadoAtaque(0, estado.jugador.vida_actual, False, [], "Sala desconocida.")
    agresor = next((e for e in sala.enemigos if e.instancia == instancia_id), None)
    if agresor is None or not agresor.vivo:
        return ResultadoAtaque(0, estado.jugador.vida_actual, False, [], "Ese enemigo no ataca.")
    defensa = estado.jugador.defensa_total(
        bonus_armadura(catalogo or {}, estado.jugador.armadura_equipada)
    )
    dano = calcular_dano(ataque_enemigo, defensa)
    estado.jugador.recibir_dano(dano)
    murio = not estado.jugador.vivo
    if murio:
        estado.estado = "derrota"
    return ResultadoAtaque(dano, estado.jugador.vida_actual, murio)
