
from __future__ import annotations

from dataclasses import dataclass

from src.controller2.agenda import Agenda, Evento

BASE_TURNO = 100

# Costos base por acción (§2.3 doc oficial).
COSTOS: dict[str, int] = {
    "mover": 100,
    "atacar": 100,
    "esperar": 100,
    "usar": 50,
    "equipar": 50,
    "recoger": 25,
    "soltar": 25,
    "abrir": 50,
}


def intervalo_por_velocidad(velocidad: int, base: int = BASE_TURNO) -> int:
    """Compatibilidad: costo 100 implícito. Preferir ``intervalo``."""
    return intervalo(100, velocidad)


def intervalo(costo: int, velocidad: int) -> int:
    """§2.3: max(1, costo*100 // velocidad)."""
    if velocidad <= 0:
        raise ValueError("velocidad debe ser > 0")
    if costo <= 0:
        raise ValueError("costo debe ser > 0")
    return max(1, int(costo) * 100 // int(velocidad))


def reescalar(t_actual: int, t_siguiente: int, v_anterior: int, v_nueva: int) -> int:
    """§2.3 cambio de velocidad: conserva progreso, asigna seq nuevo fuera."""
    if v_anterior <= 0 or v_nueva <= 0:
        raise ValueError("velocidades deben ser > 0")
    restante = max(0, int(t_siguiente) - int(t_actual))
    return int(t_actual) + max(1, restante * int(v_anterior) // int(v_nueva))


@dataclass
class RelojVirtual:
    """Tiempo virtual. Vive en ``EstadoPartida.reloj`` (K2)."""

    ahora: int = 0
    base: int = BASE_TURNO

    def __post_init__(self) -> None:
        if self.ahora < 0:
            raise ValueError("ahora no puede ser negativo")

    def intervalo(self, velocidad: int, costo: int = 100) -> int:
        return intervalo(costo, velocidad)

    def programar_turno(
        self, agenda: Agenda, actor: str, velocidad: int, datos_extra: dict | None = None,
        costo: int = 100,
    ) -> Evento:
        """Agenda el proximo turno de ``actor`` (jugador o instancia)."""
        datos = {"actor": actor, "costo": int(costo)}
        if datos_extra:
            datos.update(datos_extra)
        return agenda.programar(self.ahora + intervalo(costo, velocidad), "turno", datos)

    def reprogramar_por_velocidad(
        self, agenda: Agenda, seq: int, v_anterior: int, v_nueva: int
    ) -> Evento | None:
        """Cancela evento seq y lo reprograma con tiempo reescalado (seq nuevo)."""
        viejo = None
        for ev in agenda:
            if ev.seq == seq:
                viejo = ev
                break
        if viejo is None:
            return None
        agenda.cancelar_por_seq(seq)
        nuevo_t = reescalar(self.ahora, viejo.t, v_anterior, v_nueva)
        return agenda.programar(nuevo_t, viejo.tipo, dict(viejo.datos))

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
