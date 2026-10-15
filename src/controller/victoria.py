"""Victoria, derrota y tabla local (§2.12 doc oficial).

Derrota: vida 0. Victoria: entrar a sala_salida después de haber abierto con
la llave la puerta que da acceso. Sin fórmula de puntaje: tabla local con
nombre, cripta id+versión, acciones, enemigos derrotados, reloj final.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable

from src.controller.modelo import EstadoPartida


def hay_victoria(estado: EstadoPartida) -> bool:
    return bool(
        estado.sala_actual == estado.sala_salida
        and getattr(estado, "puerta_salida_abierta", False)
    )


def hay_derrota(estado: EstadoPartida) -> bool:
    return not estado.jugador.vivo


def actualizar_estado(estado: EstadoPartida) -> str:
    """Fija estado a victoria/derrota si corresponde. Devuelve el estado."""
    if hay_derrota(estado):
        estado.estado = "derrota"
    elif hay_victoria(estado):
        estado.estado = "victoria"
    else:
        estado.estado = "jugando"
    return estado.estado


@dataclass
class EntradaPuntaje:
    nombre: str
    cripta_id: str
    version_cripta: str
    acciones: int
    enemigos_derrotados: int
    reloj_final: int


def entrada_desde_estado(estado: EstadoPartida, nombre: str) -> EntradaPuntaje:
    return EntradaPuntaje(
        nombre=nombre,
        cripta_id=estado.cripta_id,
        version_cripta=estado.version_cripta,
        acciones=int(getattr(estado, "acciones_jugador", 0)),
        enemigos_derrotados=int(getattr(estado, "enemigos_derrotados", 0)),
        reloj_final=int(estado.reloj),
    )


def calcular_puntaje(estado: EstadoPartida, enemigos_muertos: int = 0) -> int:
    """Compat tests viejos. Ya no es puntaje oficial (tabla §2.12)."""
    return (len(estado.salas_visitadas) * 100 + enemigos_muertos * 50
            + estado.jugador.vida_actual * 10 + len(estado.jugador.inventario) * 5)


def ordenar_puntajes(puntajes: list, algoritmo: Callable[[list], list] | None = None) -> list:
    """Ordena con algoritmo propio inyectado (C2 no usa sort/sorted)."""
    if algoritmo is None:
        raise TypeError("ordenar_puntajes necesita un algoritmo propio (F9).")
    return algoritmo(list(puntajes))


def puntajes_a_dicts(entradas: list[EntradaPuntaje]) -> list[dict]:
    return [asdict(e) for e in entradas]
