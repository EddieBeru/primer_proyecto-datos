
from __future__ import annotations

from dataclasses import dataclass

from src.controller.agenda import Agenda, Evento

BASE_TURNO = 100
# TODO(profe pregunta 6): reemplazar por la formula real de tiempo-entre-turnos del enunciado.
# TODO(C2-8): guardian/errante/rastreador reutilizan este intervalo para sus turnos.


def intervalo_por_velocidad(velocidad: int, base: int = BASE_TURNO) -> int:
    """Ticks entre dos turnos de una criatura. velocidad debe ser > 0."""
    # TODO(profe pregunta 6): si velocidad 0 o negativa tiene sentido en el enunciado, ajustar validacion.
    if velocidad <= 0:
        raise ValueError("velocidad debe ser > 0")
    if base <= 0:
        raise ValueError("base debe ser > 0")
    return max(1, base // velocidad)


@dataclass
class RelojVirtual:
    """Tiempo virtual. Vive en ``EstadoPartida.reloj`` (K2)."""

    ahora: int = 0
    base: int = BASE_TURNO

    def __post_init__(self) -> None:
        if self.ahora < 0:
            raise ValueError("ahora no puede ser negativo")

    def intervalo(self, velocidad: int) -> int:
        return intervalo_por_velocidad(velocidad, self.base)

    def programar_turno(
        self, agenda: Agenda, actor: str, velocidad: int, datos_extra: dict | None = None
    ) -> Evento:
        """Agenda el proximo turno de ``actor`` (jugador o instancia)."""
        datos = {"actor": actor}
        if datos_extra:
            datos.update(datos_extra)
        return agenda.programar(self.ahora + self.intervalo(velocidad), "turno", datos)

    def avanzar(self, agenda: Agenda) -> Evento | None:
        """Salta al siguiente evento y lo devuelve. None si agenda vacia."""
        # TODO(C2-12): la fachada debe convertir el ValueError en error amable, no cierre brusco.
        proximo = agenda.ver_proximo()
        if proximo is None:
            return None
        if proximo.t < self.ahora:
            raise ValueError(f"evento en el pasado: t={proximo.t} < ahora={self.ahora}")
        self.ahora = proximo.t
        return agenda.sacar_proximo()
