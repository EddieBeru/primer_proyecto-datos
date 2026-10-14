"""Comportamiento de enemigos y rastro: guardian, errante, rastreador.

Determinismo: mismas acciones -> misma decision. El errante elige por
(reloj + suma de ord(instancia)) % vecinas; el rastreador va a la vecina
con mayor rastro (empate: menor id). Sin aleatorios.
"""

from __future__ import annotations

from src.controller.agenda import Agenda
from src.controller.modelo import EstadoPartida
from src.controller.reloj import RelojVirtual

COMPORTAMIENTOS = ("guardián", "errante", "rastreador")


def comportamiento_de(catalogo: dict | None, tipo_id: str) -> str:
    # TODO(C1-7): el comportamiento viene de la ficha del catalogo (lote de 10).
    ficha = (catalogo or {}).get(tipo_id)
    comp = getattr(ficha, "comportamiento", "guardián")
    return comp if comp in COMPORTAMIENTOS else "guardián"


def velocidad_de(catalogo: dict | None, tipo_id: str, defecto: int = 5) -> int:
    ficha = (catalogo or {}).get(tipo_id)
    vel = int(getattr(ficha, "velocidad", defecto) or defecto)
    return vel if vel > 0 else defecto


def _vecinas(estado: EstadoPartida, sala_id: int) -> list[int]:
    sala = estado.salas.get(sala_id)
    if sala is None:
        return []
    return sorted({s.destino for s in sala.salidas.values()})


def decidir_destino(estado: EstadoPartida, instancia_id: str,
                    catalogo: dict | None = None, ahora: int = 0) -> int | None:
    """Sala destino o None (quedarse). Nunca usa azar."""
    # TODO(profe pregunta 7): confirmar regla de frescura/duracion del rastro.
    actual = None
    for sala in estado.salas.values():
        for e in sala.enemigos:
            if e.instancia == instancia_id and e.vivo:
                actual = e
                break
    if actual is None:
        return None
    comp = comportamiento_de(catalogo, actual.tipo_id)
    vecinas = [v for v in _vecinas(estado, actual.sala_actual) if v in estado.salas]
    if comp == "guardián" or not vecinas:
        return None
    if comp == "rastreador":
        mejor = max(vecinas, key=lambda v: (estado.salas[v].rastro, -v))
        if estado.salas[mejor].rastro > 0:
            return mejor
    idx = (ahora + sum(ord(c) for c in instancia_id)) % len(vecinas)
    return vecinas[idx]


def mover_enemigo(estado: EstadoPartida, instancia_id: str, destino: int) -> bool:
    """Mueve la instancia entre salas (errante/rastreador)."""
    # TODO(C2-9): guardar sala origen como inversa.
    # TODO(C2-11): anotar movimiento a bitacora (K3) con instancia (replay sin ambiguedad).
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
    for sala in estado.salas.values():
        sala.rastro = max(0, sala.rastro - cantidad)


def turno_enemigo(estado: EstadoPartida, agenda: Agenda, reloj: RelojVirtual,
                  instancia_id: str, catalogo: dict | None = None) -> str:
    """Ejecuta un turno: decide, mueve y reprograma el siguiente."""
    destino = decidir_destino(estado, instancia_id, catalogo, reloj.ahora)
    if destino is not None:
        mover_enemigo(estado, instancia_id, destino)
    tipo = next((e.tipo_id for s in estado.salas.values()
                 for e in s.enemigos if e.instancia == instancia_id), None)
    if tipo is not None:
        reloj.programar_turno(agenda, instancia_id, velocidad_de(catalogo, tipo),
                              {"kind": "enemigo", "tipo": tipo})
    decaer_rastro(estado, 1)
    return f"{instancia_id}->" + (str(destino) if destino is not None else "quieto")
