"""Bitacora K3 y --replay: una linea por hecho, formato fijo.

Formato: reloj|tipo|actor|detalle (detalle sin '|' ni saltos).
El que escribe es C2; el que guarda/lee el archivo es C1 (C1-9).
Aqui solo vive el formato + un puerto en memoria para probar sin archivos.
"""

from __future__ import annotations

from typing import Protocol

TIPOS = {"mover", "atacar", "abrir", "recoger", "soltar", "equipar", "efecto",
         "dano", "muerte", "victoria", "derrota", "deshacer"}


def formatear(reloj: int, tipo: str, actor: str, detalle: str = "") -> str:
    """Crea una linea valida. Lanza ValueError si el tipo o '|' son invalidos."""
    # TODO(C1-9/regla 6.3): no cambiar este formato sin avisar a C1 (rompe --replay).
    # TODO(profe pregunta 10): si hay formato obligatorio, reemplazar este.
    if tipo not in TIPOS:
        raise ValueError(f"tipo de bitacora invalido: {tipo}")
    for campo in (actor, detalle):
        if "|" in campo or "\n" in campo:
            raise ValueError("actor/detalle no pueden tener '|' ni saltos")
    return f"{int(reloj)}|{tipo}|{actor}|{detalle}"


def parsear(linea: str) -> dict:
    """Linea -> {reloj, tipo, actor, detalle}. Lanza ValueError si es invalida."""
    partes = linea.rstrip("\n").split("|")
    if len(partes) != 4:
        raise ValueError(f"linea invalida: {linea!r}")
    reloj, tipo, actor, detalle = partes
    if tipo not in TIPOS:
        raise ValueError(f"tipo desconocido: {tipo}")
    return {"reloj": int(reloj), "tipo": tipo, "actor": actor, "detalle": detalle}


class PuertoBitacora(Protocol):
    """Lo que C2 le pide a C1 (K3): anotar y leer lineas en orden."""

    def anotar(self, linea: str) -> None: ...
    def leer(self) -> list[str]: ...


class BitacoraMemoria:
    """Puerto en memoria (para probar replay sin archivos). C1-9 la reemplaza."""

    def __init__(self, lineas: list[str] | None = None) -> None:
        self._lineas: list[str] = list(lineas or [])

    def anotar(self, linea: str) -> None:
        parsear(linea)  # valida antes de guardar
        self._lineas.append(linea)

    def leer(self) -> list[str]:
        return list(self._lineas)


def reproducir(fachada, lineas: list[str]) -> None:
    """Vuelve a ejecutar lineas sobre una fachada fresca. Mismo resultado = OK."""
    # TODO(C1-9): las lineas las entrega C1 leyendo el archivo; aqui solo se ejecutan.
    for linea in lineas:
        hecho = parsear(linea)
        tipo, detalle = hecho["tipo"], hecho["detalle"]
        if tipo == "mover":
            fachada.mover(detalle)
        elif tipo == "atacar":
            fachada.atacar(detalle)
        elif tipo == "recoger":
            fachada.recoger(detalle)
        elif tipo == "soltar":
            fachada.soltar(int(detalle) if detalle.isdigit() else detalle)
        elif tipo == "equipar":
            fachada.equipar(int(detalle) if detalle.isdigit() else 0)
        elif tipo == "deshacer":
            fachada.deshacer()
