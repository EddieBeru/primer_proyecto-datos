from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.controller2.modelo import EstadoPartida, SalaViva
from src.controller2.agenda import Agenda, Evento
from src.controller2.reloj import RelojVirtual


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


@dataclass
class ResultadoApertura:
    ok: bool
    mensaje: str
    evento_cierre_seq: int | None = None


def abrir_puerta(
    estado: EstadoPartida, direccion: str, agenda: Agenda, reloj: RelojVirtual
) -> ResultadoApertura:
    """§2.5: abrir es acción costo 50, distinta de atravesar. Llave no consume."""
    try:
        actual = estado.salas[estado.sala_actual]
    except KeyError:
        return ResultadoApertura(False, "Sala actual desconocida.")
    salida = actual.salidas.get(direccion)
    if salida is None:
        return ResultadoApertura(False, "No hay camino por ahí.")
    if not salida.cerrada:
        return ResultadoApertura(True, "Ya estaba abierta.")
    if salida.llave is None:
        return ResultadoApertura(False, "Está trabada.")
    if not estado.jugador.tiene_llave(salida.llave):
        return ResultadoApertura(False, f"Necesitas la llave {salida.llave}.")
    salida.cerrada = False
    # §2.12: marca si se abrió la puerta que da acceso a la salida.
    if salida.destino == estado.sala_salida:
        estado.puerta_salida_abierta = True
    evento_seq: int | None = None
    if salida.cierre_automatico is not None:
        ev: Evento = agenda.programar(
            reloj.ahora + int(salida.cierre_automatico),
            "cierre_puerta",
            {"sala": actual.id, "direccion": direccion},
        )
        evento_seq = ev.seq
    return ResultadoApertura(True, "", evento_seq)


def intentar_mover(
    estado: EstadoPartida,
    direccion: str,
    proveedor: ProveedorSalas,
    agenda: Agenda,
    reloj: RelojVirtual,
) -> ResultadoMovimiento:
    """§2.5: moverse costo 100, exige puerta abierta. Pide contenido antes."""
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
        return ResultadoMovimiento(False, f"Puerta cerrada. Ábrela con {salida.llave}.")
    try:
        destino = estado.salas[salida.destino]
    except KeyError:
        try:
            destino = proveedor.sala_lista(salida.destino)
        except Exception as e:  # proveedor informa 404/sin red/presupuesto (K4)
            return ResultadoMovimiento(False, f"No se pudo entrar a la sala: {e}")
        estado.registrar_sala(destino)
    destino.visitada = True
    estado.sala_actual = destino.id
    # §2.9: destino recibe tiempo actual; activa dormidos §2.4.
    destino.ultima_visita = reloj.ahora
    try:
        from src.controller2.enemigos import activar_sala
        activar_sala(estado, agenda, reloj.ahora, destino.id, None)
    except Exception:
        pass
    return ResultadoMovimiento(True, "", destino.id, False, None)


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
