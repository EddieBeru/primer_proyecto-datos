"""Efectos con el paso del tiempo (§2.10 doc oficial).

Veneno: daño cada 80, dura 400 salvo antídoto. Trampa: rearme 300 default.
Regeneración: cada 200 sin pasar vida_max. Cambio velocidad reescala turno.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.controller.agenda import Agenda
from src.controller.modelo import EstadoPartida
from src.controller.reloj import RelojVirtual


@dataclass
class ResultadoEfecto:
    ok: bool
    mensaje: str = ""
    dano: int = 0
    eventos: list[int] = field(default_factory=list)


VENENO_PERIODO = 80
VENENO_DURACION = 400
REARME_TRAMPA_DEFAULT = 300
REGENERACION_PERIODO = 200


def _ficha(catalogo: dict | None, tipo_id: str):
    return (catalogo or {}).get(tipo_id)


def _consumir(estado: EstadoPartida, item_id: str) -> bool:
    # TODO(C2-9): guardar la posicion consumida como inversa (tope 5).
    # TODO(C2-11): anotar consumo a bitacora (K3).
    if item_id in estado.jugador.inventario:
        estado.jugador.inventario.remove(item_id)
        return True
    return False


def pisar_trampa(estado: EstadoPartida, agenda: Agenda, reloj: RelojVirtual,
                 instancia_id: str, catalogo: dict | None = None) -> tuple[ResultadoEfecto, dict | None]:
    """Activa trampa armada. Desarma y programa rearme (300 default §2.10)."""
    sala = estado.salas.get(estado.sala_actual)
    if sala is None:
        return ResultadoEfecto(False, "Sala desconocida."), None
    trampa = next((t for t in sala.trampas if t.instancia == instancia_id), None)
    if trampa is None:
        return ResultadoEfecto(False, "Esa trampa no está aquí."), None
    if not trampa.armada:
        return ResultadoEfecto(True, "Ya estaba desarmada."), None
    ficha = _ficha(catalogo, trampa.tipo_id)
    dano = int(getattr(ficha, "dano", 0) or 0)
    rearme = getattr(ficha, "rearme", None)
    rearme = int(rearme) if rearme is not None else REARME_TRAMPA_DEFAULT
    vida_antes = estado.jugador.vida_actual
    estado.jugador.recibir_dano(dano)
    trampa.armada = False
    eventos: list[int] = []
    ev = agenda.programar(reloj.ahora + rearme, "rearme_trampa", {"instancia": trampa.instancia})
    eventos.append(ev.seq)
    if not estado.jugador.vivo:
        estado.estado = "derrota"
    inversa = {"op": "trampa", "datos": {"instancia": trampa.instancia,
               "armada_antes": True, "vida_antes": vida_antes}, "eventos": eventos}
    return ResultadoEfecto(True, "", dano, eventos), inversa


def ejecutar_rearme(estado: EstadoPartida, instancia_id: str) -> bool:
    for sala in estado.salas.values():
        for t in sala.trampas:
            if t.instancia == instancia_id:
                t.armada = True
                return True
    return False


def envenenar(estado: EstadoPartida, agenda: Agenda, reloj: RelojVirtual,
              dano_por_tick: int) -> list[int]:
    """§2.10: pulsos cada 80 durante 400 (5 pulsos) salvo antídoto."""
    seqs = []
    for i in range(1, VENENO_DURACION // VENENO_PERIODO + 1):
        ev = agenda.programar(reloj.ahora + i * VENENO_PERIODO, "veneno", {"dano": dano_por_tick})
        seqs.append(ev.seq)
    estado.jugador.efectos["veneno"] = estado.jugador.efectos.get("veneno", 0) + VENENO_DURACION
    return seqs


def envenenar_legacy(estado: EstadoPartida, agenda: Agenda, reloj: RelojVirtual,
                     ticks: int, dano_por_tick: int) -> list[int]:
    """Compat tests viejos: ticks genéricos de 1 unidad."""
    seqs = []
    for i in range(1, max(0, int(ticks)) + 1):
        ev = agenda.programar(reloj.ahora + i, "veneno", {"dano": dano_por_tick})
        seqs.append(ev.seq)
    estado.jugador.efectos["veneno"] = estado.jugador.efectos.get("veneno", 0) + max(0, int(ticks))
    return seqs


def ejecutar_veneno(estado: EstadoPartida, dano: int) -> bool:
    """Un tick de veneno: dana y descuenta. Devuelve si sigue envenenado."""
    estado.jugador.recibir_dano(dano)
    if not estado.jugador.vivo:
        estado.estado = "derrota"
    rest = estado.jugador.efectos.get("veneno", 0)
    paso = VENENO_PERIODO if rest >= VENENO_PERIODO else 1
    rest = rest - paso
    if rest <= 0:
        estado.jugador.efectos.pop("veneno", None)
        return False
    estado.jugador.efectos["veneno"] = rest
    return True


def ejecutar_regeneracion(estado: EstadoPartida, instancia_id: str, cantidad: int,
                          vida_max: int | None = None) -> bool:
    """§2.10: recupera sin superar vida_max."""
    for sala in estado.salas.values():
        for e in sala.enemigos:
            if e.instancia == instancia_id and e.vivo:
                e.vida_actual = e.vida_actual + max(0, int(cantidad))
                if vida_max is not None:
                    e.vida_actual = min(int(vida_max), e.vida_actual)
                return True
    return False


def aplicar_cambio_velocidad(estado: EstadoPartida, agenda: Agenda, reloj: RelojVirtual,
                             v_anterior: int, v_nueva: int, actor: str = "jugador") -> None:
    """§2.3: reescala próxima acción programada del actor (seq nuevo)."""
    seqs = [ev.seq for ev in agenda if (ev.datos or {}).get("actor") == actor]
    for seq in seqs:
        reloj.reprogramar_por_velocidad(agenda, seq, v_anterior, v_nueva)


def usar_pocion(estado: EstadoPartida, agenda: Agenda, reloj: RelojVirtual,
                pocion_id: str, catalogo: dict | None = None) -> tuple[ResultadoEfecto, dict | None]:
    """Cura de inmediato; si trae modificador+duracion programa su fin."""
    # TODO(profe pregunta 3): confirmar que cura/mod/duracion vacios = sin efecto (DEFAULTS).
    ficha = _ficha(catalogo, pocion_id)
    if ficha is None and catalogo:
        return ResultadoEfecto(False, "Poción desconocida."), None
    if pocion_id not in estado.jugador.inventario:
        return ResultadoEfecto(False, "No la tienes."), None
    cura = int(getattr(ficha, "cura", 0) or 0)
    mod = int(getattr(ficha, "modificador_velocidad", 0) or 0)
    dur = int(getattr(ficha, "duracion", 0) or 0)
    vida_antes = estado.jugador.vida_actual
    vel_antes = estado.jugador.efectos.get("veloz", 0)
    _consumir(estado, pocion_id)
    estado.jugador.curar(cura)
    eventos: list[int] = []
    if mod and dur:
        estado.jugador.efectos["veloz"] = dur
        ev = agenda.programar(reloj.ahora + dur, "fin_efecto", {"efecto": "veloz"})
        eventos.append(ev.seq)
    inversa = {"op": "pocion", "datos": {"item": pocion_id, "vida_antes": vida_antes,
               "veloz_antes": vel_antes}, "eventos": eventos}
    return ResultadoEfecto(True, "", cura, eventos), inversa


def usar_antidoto(estado: EstadoPartida, agenda: Agenda, antidoto_id: str) -> tuple[ResultadoEfecto, dict | None]:
    """Quita el veneno y cancela sus eventos pendientes."""
    if antidoto_id not in estado.jugador.inventario:
        return ResultadoEfecto(False, "No lo tienes."), None
    veneno_antes = estado.jugador.efectos.get("veneno", 0)
    _consumir(estado, antidoto_id)
    estado.jugador.efectos.pop("veneno", None)
    n = agenda.cancelar_donde(lambda e: e.tipo == "veneno")
    inversa = {"op": "antidoto", "datos": {"item": antidoto_id, "veneno_antes": veneno_antes}, "eventos": []}
    return ResultadoEfecto(True, f"Veneno curado ({n} ticks cancelados)."), inversa


def usar_antorcha(estado: EstadoPartida, agenda: Agenda, reloj: RelojVirtual,
                  antorcha_id: str, catalogo: dict | None = None) -> tuple[ResultadoEfecto, dict | None]:
    ficha = _ficha(catalogo, antorcha_id)
    dur = int(getattr(ficha, "duracion", 0) or 0)
    if antorcha_id not in estado.jugador.inventario:
        return ResultadoEfecto(False, "No la tienes."), None
    _consumir(estado, antorcha_id)
    estado.jugador.efectos["antorcha"] = dur
    ev = agenda.programar(reloj.ahora + dur, "fin_efecto", {"efecto": "antorcha"})
    inversa = {"op": "antorcha", "datos": {"item": antorcha_id}, "eventos": [ev.seq]}
    return ResultadoEfecto(True, "", 0, [ev.seq]), inversa


def ejecutar_fin_efecto(estado: EstadoPartida, nombre: str) -> bool:
    return estado.jugador.efectos.pop(nombre, None) is not None
