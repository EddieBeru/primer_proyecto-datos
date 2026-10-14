"""Victoria, derrota y puntaje.

Victoria: sala_actual == sala_salida con llave_salida en inventario.
Derrota: vida en 0 (la marca combate/efectos; aqui solo se consulta).
Puntaje: supuesto explicito pendiente del profe (pregunta 9).
"""

from __future__ import annotations

from typing import Callable

from src.controller.modelo import EstadoPartida


def hay_victoria(estado: EstadoPartida) -> bool:
    return estado.sala_actual == estado.sala_salida and estado.llave_salida in estado.jugador.inventario


def hay_derrota(estado: EstadoPartida) -> bool:
    return not estado.jugador.vivo


def actualizar_estado(estado: EstadoPartida) -> str:
    """Fija estado a victoria/derrota si corresponde. Devuelve el estado."""
    # TODO(C2-12): la fachada llama esto tras cada intencion y cambia de pantalla.
    if hay_derrota(estado):
        estado.estado = "derrota"
    elif hay_victoria(estado):
        estado.estado = "victoria"
    else:
        estado.estado = "jugando"
    return estado.estado


def calcular_puntaje(estado: EstadoPartida, enemigos_muertos: int = 0) -> int:
    """Supuesto: salas*100 + muertos*50 + vida*10 + inventario*5. Determinista."""
    # TODO(profe pregunta 9): reemplazar por la formula real del enunciado.
    return (len(estado.salas_visitadas) * 100 + enemigos_muertos * 50
            + estado.jugador.vida_actual * 10 + len(estado.jugador.inventario) * 5)


def ordenar_puntajes(puntajes: list, algoritmo: Callable[[list], list] | None = None) -> list:
    """Ordena con el mergesort de C1-11 inyectado (C2 no usa sort/sorted)."""
    # TODO(C1-11): pasar el mergesort real cuando este listo.
    if algoritmo is None:
        raise TypeError("ordenar_puntajes necesita el mergesort de C1 (C1-11).")
    return algoritmo(list(puntajes))
