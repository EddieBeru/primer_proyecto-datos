
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.controller.c2_1_modelo import EstadoPartida, SalaViva
from src.controller.c2_2_agenda import Agenda, Evento
from src.controller.c2_3_reloj import RelojVirtual

RASTRO_FRESCO = 10


class ProveedorSalas(Protocol):
    """Contrato K1 minimo que C2 necesita de C1 (falso o real)."""

    def sala_lista(self, n: int) -> SalaViva: ...


@dataclass
class ResultadoMovimiento:
    ok: bool
    mensaje: str
    sala: int | None = None
    abrio_puerta: bool = False
    evento_cierre_seq: int | None = None


def intentar_mover(
    estado: EstadoPartida,
    direccion: str,
    proveedor: ProveedorSalas,
    agenda: Agenda,
    reloj: RelojVirtual,
) -> ResultadoMovimiento:
    """Flujo E completo. No lanza por sala inexistente: la pide al proveedor."""
    try:
        actual = estado.salas[estado.sala_actual]
    except KeyError:
        return ResultadoMovimiento(False, "Sala actual desconocida.")
    salida = actual.salidas.get(direccion)
    if salida is None:
        return ResultadoMovimiento(False, "No hay camino por ahí.")
    if salida.cerrada:
        if salida.llave is None:
            return ResultadoMovimiento(False, "Está trabada.")
        if not estado.jugador.tiene_llave(salida.llave):
            return ResultadoMovimiento(False, f"Necesitas la llave {salida.llave}.")
        salida.cerrada = False
        abrio = True
    else:
        abrio = False
    evento_seq: int | None = None
    if abrio and salida.cierre_automatico is not None:
        ev: Evento = agenda.programar(
            reloj.ahora + salida.cierre_automatico,
            "cierre_puerta",
            {"sala": actual.id, "direccion": direccion},
        )
        evento_seq = ev.seq
    origen = estado.sala_actual
    try:
        destino = proveedor.sala_lista(salida.destino)
    except Exception as e:  # proveedor informa 404/sin red/presupuesto (K4)
        if abrio:  # revierte apertura para no dejar estado a medias
            salida.cerrada = True
            if evento_seq is not None:
                agenda.cancelar_por_seq(evento_seq)
        return ResultadoMovimiento(False, f"No se pudo entrar a la sala: {e}")
    estado.registrar_sala(destino)
    destino.visitada = True
    estado.salas[origen].rastro = RASTRO_FRESCO
    estado.sala_actual = destino.id
    return ResultadoMovimiento(True, "", destino.id, abrio, evento_seq)


def ejecutar_cierre(estado: EstadoPartida, sala_id: int, direccion: str) -> bool:
    """Cierra la puerta (la llama el motor cuando la agenda dispara el evento)."""
    sala = estado.salas.get(sala_id)
    if sala is None:
        return False
    salida = sala.salidas.get(direccion)
    if salida is None:
        return False
    salida.cerrada = True
    return True
