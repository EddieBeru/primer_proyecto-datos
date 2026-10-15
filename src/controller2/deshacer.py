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


def _es_pergamino(item_id: str) -> bool:
    return "pergamino" in str(item_id) or "retroceso" in str(item_id)


def aplicar_inversa(estado, agenda, inversa: dict[str, Any]) -> bool:
    """Revierte UNA entrada y cancela sus eventos. §2.11: pergaminos excluidos."""
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
    if op == "abrir":
        s = estado.salas.get(d.get("sala"))
        if s and d.get("direccion") in s.salidas:
            s.salidas[d["direccion"]].cerrada = True
            if s.salidas[d["direccion"]].destino == estado.sala_salida:
                estado.puerta_salida_abierta = False
        return True
    if op == "dano_enemigo":
        for sala in estado.salas.values():
            for e in sala.enemigos:
                if e.instancia == d["instancia"]:
                    e.vida_actual = d["vida_antes"]
                    for b in (d.get("botin") or []):
                        if _es_pergamino(b):
                            continue
                        _quitar_del_suelo(estado, b)
                    return True
        return False
    if op in ("dano_jugador", "veneno_tick"):
        estado.jugador.vida_actual = d["vida_antes"]
        if estado.jugador.vivo and estado.estado == "derrota":
            estado.estado = "jugando"
        return True
    if op == "recoger":
        if _es_pergamino(d["item"]):
            return True  # §2.11: pergaminos fuera de reversión.
        if d["item"] in estado.jugador.inventario:
            estado.jugador.inventario.remove(d["item"])
        if d.get("sala") in estado.salas:
            estado.salas[d["sala"]].objetos_suelo.insert(d.get("pos_suelo", 0), d["item"])
        return True
    if op == "soltar":
        if _es_pergamino(d["item"]):
            return True
        if d.get("sala") in estado.salas and d["item"] in estado.salas[d["sala"]].objetos_suelo:
            estado.salas[d["sala"]].objetos_suelo.remove(d["item"])
        estado.jugador.inventario.insert(d.get("pos_inv", 0), d["item"])
        return True
    if op == "equipar":
        estado.jugador.inventario = list(d["orden_antes"])
        if "arma_antes" in d:
            estado.jugador.arma_equipada = d["arma_antes"]
            estado.jugador.armadura_equipada = d["armadura_antes"]
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
        if not _es_pergamino(d["item"]) and d["item"] not in estado.jugador.inventario:
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
    if op == "cierre":
        s = estado.salas.get(d.get("sala"))
        if s and d.get("direccion") in s.salidas and d.get("cerrada_antes") is not None:
            s.salidas[d["direccion"]].cerrada = bool(d["cerrada_antes"])
        return True
    if op == "rearme":
        for sala in estado.salas.values():
            for t in sala.trampas:
                if t.instancia == d.get("instancia"):
                    t.armada = False
        return True
    if op == "fin_efecto":
        if d.get("valor_antes") is not None:
            estado.jugador.efectos[d["efecto"]] = d["valor_antes"]
        else:
            estado.jugador.efectos.pop(d.get("efecto", ""), None)
        return True
    if op == "regeneracion":
        for sala in estado.salas.values():
            for e in sala.enemigos:
                if e.instancia == d.get("instancia"):
                    e.vida_actual = d.get("vida_antes", e.vida_actual)
                    return True
        return False
    if op == "aparece":
        inst = d.get("instancia")
        for sala in estado.salas.values():
            sala.enemigos = [e for e in sala.enemigos if e.instancia != inst]
        agenda.cancelar_donde(lambda ev: (ev.datos or {}).get("actor") == inst)
        for seq in (d.get("eventos") or []):
            agenda.cancelar_por_seq(seq)
        return True
    if op == "mover_enemigo":
        origen, destino = d.get("origen"), d.get("destino")
        for sala in estado.salas.values():
            for e in sala.enemigos:
                if e.instancia == d.get("instancia"):
                    sala.enemigos = [x for x in sala.enemigos if x.instancia != d["instancia"]]
                    e.sala_actual = origen
                    if origen in estado.salas:
                        estado.salas[origen].enemigos.append(e)
                    return True
        return False
    return False


# Ops de acción del jugador: deshacer sigue hasta revertir una de estas (§2.11 intervalo).
_OPS_JUGADOR = {"mover", "abrir", "dano_enemigo", "recoger", "soltar", "equipar",
                "trampa", "pocion", "antidoto", "antorcha"}


def deshacer_una(estado, agenda, pila: PilaDeshacer, catalogo: dict | None = None) -> tuple[bool, str]:
    """Usa 1 pergamino: revierte última acción jugador + todo su intervalo posterior."""
    if pila.vacia:
        return False, "Nada que deshacer."
    pergamino = None
    for item in estado.jugador.inventario:
        ficha = (catalogo or {}).get(item)
        if getattr(ficha, "clase", "") == "pergamino_retroceso" or item == "pergamino":
            pergamino = item
            break
    if pergamino is None and "pergamino" not in estado.jugador.inventario:
        cand = [i for i in estado.jugador.inventario if "pergamino" in i or "retroceso" in i]
        pergamino = cand[0] if cand else None
    if pergamino is None:
        return False, "Sin pergaminos."
    estado.jugador.inventario.remove(pergamino)
    # §2.11: el consumo queda fuera de la reversión (no se restaura).
    ok_any = False
    while not pila.vacia:
        inversa = pila.desapilar()
        if inversa is None:
            break
        ok = aplicar_inversa(estado, agenda, inversa)
        ok_any = ok_any or ok
        if (inversa.get("op") in _OPS_JUGADOR):
            break
    return ok_any, "" if ok_any else "No se pudo revertir."
