"""Deshacer con pergamino de retroceso: pila de acciones inversas (tope 5).

Cada accion guarda QUE cambio (no copia total). Al deshacer tambien se
cancelan los eventos de agenda que esa accion creo (por sus seqs).
El pergamino se consume (uno del inventario por cada deshacer).
"""

from __future__ import annotations

from typing import Any, Iterator


class _NodoPila:
    __slots__ = ("inversa", "siguiente")

    def __init__(self, inversa: dict[str, Any]) -> None:
        self.inversa = inversa
        self.siguiente: _NodoPila | None = None


class PilaDeshacer:
    """Pila propia sobre lista enlazada. Tope 5: al llenarse se olvida la mas vieja."""

    TOPE = 5

    # TODO(C1-8/K2): a_lista/desde_lista es lo que se guarda en EstadoPartida.pila_deshacer.
    def __init__(self, inversas: list[dict[str, Any]] | None = None) -> None:
        self._cima: _NodoPila | None = None
        self._len = 0
        for inv in inversas or []:
            self.apilar(inv)

    def __len__(self) -> int:
        return self._len

    @property
    def vacia(self) -> bool:
        return self._cima is None

    def apilar(self, inversa: dict[str, Any]) -> None:
        nodo = _NodoPila(dict(inversa))
        nodo.siguiente = self._cima
        self._cima = nodo
        self._len += 1
        if self._len > self.TOPE:
            # olvida la mas vieja (fondo): recorre hasta el penultimo
            actual = self._cima
            while actual.siguiente is not None and actual.siguiente.siguiente is not None:
                actual = actual.siguiente
            actual.siguiente = None
            self._len = self.TOPE

    def desapilar(self) -> dict[str, Any] | None:
        if self._cima is None:
            return None
        inv = self._cima.inversa
        self._cima = self._cima.siguiente
        self._len -= 1
        return inv

    def __iter__(self) -> Iterator[dict[str, Any]]:
        n = self._cima
        while n is not None:
            yield n.inversa
            n = n.siguiente

    def a_lista(self) -> list[dict[str, Any]]:
        return [dict(i) for i in self]

    @classmethod
    def desde_lista(cls, items: list[dict[str, Any]]) -> "PilaDeshacer":
        pila = cls()
        for inv in reversed(items):  # items vienen cima-primero
            pila.apilar(inv)
        return pila


def _quitar_del_suelo(estado, item_id: str) -> None:
    sala = estado.salas.get(estado.sala_actual)
    if sala and item_id in sala.objetos_suelo:
        sala.objetos_suelo.remove(item_id)


def aplicar_inversa(estado, agenda, inversa: dict[str, Any]) -> bool:
    """Revierte UNA accion y cancela sus eventos. Devuelve True si pudo."""
    # TODO(C2-4..C2-8): cada accion nueva debe agregar aqui su `op` con su inversa.
    for seq in (inversa.get("eventos") or []):
        agenda.cancelar_por_seq(seq)
    op = inversa.get("op")
    d = inversa.get("datos") or {}
    if op == "mover":
        estado.sala_actual = d["origen"]
        if d.get("abrio"):
            s = estado.salas.get(d["sala_puerta"])
            if s and d.get("direccion") in s.salidas:
                s.salidas[d["direccion"]].cerrada = True
        return True
    if op == "dano_enemigo":
        for sala in estado.salas.values():
            for e in sala.enemigos:
                if e.instancia == d["instancia"]:
                    e.vida_actual = d["vida_antes"]
                    for b in (d.get("botin") or []):
                        _quitar_del_suelo(estado, b)
                    return True
        return False
    if op == "dano_jugador":
        estado.jugador.vida_actual = d["vida_antes"]
        if estado.jugador.vivo and estado.estado == "derrota":
            estado.estado = "jugando"
        return True
    if op == "recoger":
        if d["item"] in estado.jugador.inventario:
            estado.jugador.inventario.remove(d["item"])
        estado.salas[d["sala"]].objetos_suelo.insert(d.get("pos_suelo", 0), d["item"])
        return True
    if op == "soltar":
        if d["item"] in estado.salas[d["sala"]].objetos_suelo:
            estado.salas[d["sala"]].objetos_suelo.remove(d["item"])
        estado.jugador.inventario.insert(d.get("pos_inv", 0), d["item"])
        return True
    if op == "equipar":
        estado.jugador.inventario = list(d["orden_antes"])
        return True
    if op == "trampa":
        for sala in estado.salas.values():
            for t in sala.trampas:
                if t.instancia == d["instancia"]:
                    t.armada = d.get("armada_antes", True)
        estado.jugador.vida_actual = d["vida_antes"]
        if estado.jugador.vivo and estado.estado == "derrota":
            estado.estado = "jugando"
        return True
    if op in ("pocion", "antidoto", "antorcha"):
        estado.jugador.inventario.append(d["item"])
        if "vida_antes" in d:
            estado.jugador.vida_actual = d["vida_antes"]
        if "veloz_antes" in d:
            if d["veloz_antes"]:
                estado.jugador.efectos["veloz"] = d["veloz_antes"]
            else:
                estado.jugador.efectos.pop("veloz", None)
        if op == "antidoto" and d.get("veneno_antes"):
            estado.jugador.efectos["veneno"] = d["veneno_antes"]
        return True
    return False


def deshacer_una(estado, agenda, pila: PilaDeshacer, catalogo: dict | None = None) -> tuple[bool, str]:
    """Deshace 1 accion si hay pila y hay pergamino. Consume 1 pergamino."""
    # TODO(C2-11): anotar el deshacer a bitacora (K3) como hecho propio.
    if pila.vacia:
        return False, "Nada que deshacer."
    pergamino = None
    for item in estado.jugador.inventario:
        ficha = (catalogo or {}).get(item)
        if getattr(ficha, "clase", "") == "pergamino_retroceso" or item == "pergamino":
            pergamino = item
            break
    if pergamino is None and "pergamino" not in estado.jugador.inventario:
        # sin catalogo a mano: acepta cualquier id que contenga la palabra
        cand = [i for i in estado.jugador.inventario if "pergamino" in i or "retroceso" in i]
        pergamino = cand[0] if cand else None
    if pergamino is None:
        return False, "Sin pergaminos."
    inversa = pila.desapilar()
    if inversa is None:
        return False, "Nada que deshacer."
    estado.jugador.inventario.remove(pergamino)
    ok = aplicar_inversa(estado, agenda, inversa)
    return ok, "" if ok else "No se pudo revertir."
