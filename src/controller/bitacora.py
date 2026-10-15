"""Bitacora K3 y --replay (§4.11 doc oficial).

Header primera línea: ``#cripta <id> <version_cripta> <version_catalogo> <semilla>``.
Resto: ``reloj|tipo|actor|detalle``. Replay valida versiones contra estado
actual y rehúsa reproducir silenciosamente contra datos distintos.
"""

from __future__ import annotations

from typing import Protocol

TIPOS = {"mover", "atacar", "abrir", "recoger", "soltar", "equipar", "efecto",
         "dano", "muerte", "victoria", "derrota", "deshacer", "esperar", "usar"}


def formatear(reloj: int, tipo: str, actor: str, detalle: str = "") -> str:
    """Crea una linea valida. Lanza ValueError si el tipo o '|' son invalidos."""
    if tipo not in TIPOS:
        raise ValueError(f"tipo de bitacora invalido: {tipo}")
    for campo in (actor, detalle):
        if "|" in campo or "\n" in campo:
            raise ValueError("actor/detalle no pueden tener '|' ni saltos")
    return f"{int(reloj)}|{tipo}|{actor}|{detalle}"


def formatear_header(cripta_id: str, version_cripta: str, version_catalogo: str,
                     semilla: int) -> str:
    return f"#cripta {cripta_id} {version_cripta} {version_catalogo} {int(semilla)}"


def parsear_header(linea: str) -> dict:
    p = linea.strip().split()
    if len(p) != 5 or p[0] != "#cripta":
        raise ValueError(f"header invalido: {linea!r}")
    _, cid, vcrip, vcat, sem = p
    return {"cripta_id": cid, "version_cripta": vcrip,
            "version_catalogo": vcat, "semilla": int(sem)}


def parsear(linea: str) -> dict:
    """Linea -> {reloj, tipo, actor, detalle}. Lanza ValueError si es invalida."""
    if linea.startswith("#cripta"):
        return {"header": parsear_header(linea)}
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


class BitacoraIncompatibleError(ValueError):
    pass


def reproducir(fachada, lineas: list[str]) -> None:
    """Vuelve a ejecutar lineas sobre una fachada fresca. Valida header."""
    if not lineas:
        return
    idx = 0
    if lineas[0].startswith("#cripta"):
        head = parsear_header(lineas[0])
        est = fachada.estado
        if (head["cripta_id"] != est.cripta_id
                or head["version_cripta"] != est.version_cripta
                or head["version_catalogo"] != est.version_catalogo):
            raise BitacoraIncompatibleError(
                f"replay {head['cripta_id']} {head['version_cripta']}/"
                f"{head['version_catalogo']} != partida {est.cripta_id} "
                f"{est.version_cripta}/{est.version_catalogo}: no se reproduce"
            )
        idx = 1
    for linea in lineas[idx:]:
        if not linea.strip():
            continue
        hecho = parsear(linea)
        if "header" in hecho:
            continue
        tipo, detalle = hecho["tipo"], hecho["detalle"]
        if tipo == "mover":
            if detalle == "esperar":
                fachada.esperar()
            else:
                fachada.mover(detalle)
        elif tipo == "abrir":
            fachada.abrir(detalle)
        elif tipo == "atacar":
            fachada.atacar(detalle)
        elif tipo == "recoger":
            fachada.recoger(detalle)
        elif tipo == "soltar":
            fachada.soltar(int(detalle) if detalle.isdigit() else detalle)
        elif tipo == "equipar":
            fachada.equipar(int(detalle) if detalle.isdigit() else 0)
        elif tipo in ("efecto", "usar"):
            # detalle "pocion:X" / "antidoto:X" / "antorcha:X" / instancia trampa
            if detalle.startswith("pocion:"):
                fachada.usar_pocion(detalle.split(":", 1)[1])
            elif detalle.startswith("antidoto:"):
                fachada.usar_antidoto(detalle.split(":", 1)[1])
            elif detalle.startswith("antorcha:"):
                fachada.usar_antorcha(detalle.split(":", 1)[1])
            elif detalle:
                try:
                    fachada.pisar_trampa(detalle)
                except Exception:
                    pass
        elif tipo == "deshacer":
            fachada.deshacer()
        elif tipo == "esperar":
            fachada.esperar()
