"""Comportamiento de enemigos y rastro (§2.8/§2.9 doc oficial).

Si comparte sala con jugador: ataca (lo decide la fachada), no se mueve.
Si no: guardián espera, errante azar entre abiertas, rastreador vecina
abierta con rastro más fresco <400 (empate menor id).
Costo mover/atacar/esperar = 100 siempre.
"""

from __future__ import annotations

from src.controller2.agenda import Agenda
from src.controller2.modelo import EstadoPartida
from src.controller2.reloj import RelojVirtual

COMPORTAMIENTOS = ("guardián", "errante", "rastreador")
RASTRO_MAX_ANTIGUEDAD = 400


def comportamiento_de(catalogo: dict | None, tipo_id: str) -> str:
    ficha = (catalogo or {}).get(tipo_id)
    comp = getattr(ficha, "comportamiento", "guardián")
    return comp if comp in COMPORTAMIENTOS else "guardián"


def velocidad_de(catalogo: dict | None, tipo_id: str, defecto: int = 5) -> int:
    ficha = (catalogo or {}).get(tipo_id)
    vel = int(getattr(ficha, "velocidad", defecto) or defecto)
    return vel if vel > 0 else defecto


def _vecinas_abiertas(estado: EstadoPartida, sala_id: int) -> list[int]:
    sala = estado.salas.get(sala_id)
    if sala is None:
        return []
    out = []
    for salida in sala.salidas.values():
        if salida.cerrada:
            continue
        if salida.destino in estado.salas:
            out.append(salida.destino)
    return sorted(set(out))


def _sala_de(estado: EstadoPartida, instancia_id: str):
    for sala in estado.salas.values():
        for e in sala.enemigos:
            if e.instancia == instancia_id and e.vivo:
                return sala, e
    return None, None


def activar_sala(estado: EstadoPartida, agenda: Agenda, ahora: int,
                 sala_id: int, catalogo: dict | None = None) -> list:
    """Activa dormidos de sala (§2.4): costo 100 desde ahora, orden instancia."""
    sala = estado.salas.get(sala_id)
    if sala is None:
        return []
    dormidos = sorted(
        [e for e in sala.enemigos if e.vivo and not e.activa],
        key=lambda e: e.instancia,
    )
    evs = []
    for e in dormidos:
        e.activa = True
        vel = velocidad_de(catalogo, e.tipo_id)
        from src.controller2.reloj import intervalo
        ev = agenda.programar(ahora + intervalo(100, vel), "turno",
                              {"actor": e.instancia, "kind": "enemigo",
                               "tipo": e.tipo_id, "costo": 100})
        e.tiempo_siguiente = ev.t
        evs.append(ev)
    return evs


def decidir_destino(estado: EstadoPartida, instancia_id: str,
                    catalogo: dict | None = None, ahora: int = 0,
                    azar=None) -> int | None:
    """Sala destino o None (quedarse). Errante usa azar reproducible."""
    sala, actual = _sala_de(estado, instancia_id)
    if actual is None or sala is None:
        return None
    # Si comparte sala con jugador: ataca, no se mueve (§2.8).
    if sala.id == estado.sala_actual:
        return None
    comp = comportamiento_de(catalogo, actual.tipo_id)
    vecinas = _vecinas_abiertas(estado, actual.sala_actual)
    if comp == "guardián" or not vecinas:
        return None
    if comp == "rastreador":
        mejor = None
        mejor_t = None
        for v in vecinas:
            visita = estado.salas[v].ultima_visita
            if visita is None:
                continue
            if ahora - int(visita) >= RASTRO_MAX_ANTIGUEDAD:
                continue
            if mejor is None or int(visita) > int(mejor_t) or (
                int(visita) == int(mejor_t) and v < mejor
            ):
                mejor, mejor_t = v, visita
        return mejor
    # Errante: azar entre abiertas (§2.8). Sin azar inyectado: primera (tests).
    if azar is None:
        return vecinas[0]
    try:
        estado.azar_llamadas = int(getattr(estado, "azar_llamadas", 0)) + 1
    except Exception:
        pass
    return azar.choice(sorted(vecinas))


def mover_enemigo(estado: EstadoPartida, instancia_id: str, destino: int) -> bool:
    """Mueve la instancia entre salas (errante/rastreador)."""
    origen = None
    objetivo = None
    for sala in estado.salas.values():
        for e in sala.enemigos:
            if e.instancia == instancia_id:
                origen, objetivo = sala, e
                break
    if objetivo is None or destino not in estado.salas:
        return False
    if origen is not None and origen.id != destino:
        origen.enemigos = [e for e in origen.enemigos if e.instancia != instancia_id]
        objetivo.sala_actual = destino
        estado.salas[destino].enemigos.append(objetivo)
    return True


def decaer_rastro(estado: EstadoPartida, cantidad: int = 1) -> None:
    """Compat: ya no se usa (rastro es timestamp). Solo para tests viejos."""
    return None


def turno_enemigo(estado: EstadoPartida, agenda: Agenda, reloj: RelojVirtual,
                  instancia_id: str, catalogo: dict | None = None,
                  azar=None) -> str:
    """Ejecuta un turno: decide, mueve y reprograma el siguiente (costo 100)."""
    destino = decidir_destino(estado, instancia_id, catalogo, reloj.ahora, azar)
    if destino is not None:
        mover_enemigo(estado, instancia_id, destino)
    tipo = next((e.tipo_id for s in estado.salas.values()
                 for e in s.enemigos if e.instancia == instancia_id), None)
    if tipo is not None:
        ev = reloj.programar_turno(agenda, instancia_id, velocidad_de(catalogo, tipo),
                                   {"kind": "enemigo", "tipo": tipo}, costo=100)
        for s in estado.salas.values():
            for e in s.enemigos:
                if e.instancia == instancia_id:
                    e.tiempo_siguiente = ev.t
    return f"{instancia_id}->" + (str(destino) if destino is not None else "quieto")
