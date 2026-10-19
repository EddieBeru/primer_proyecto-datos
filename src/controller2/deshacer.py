"""Deshacer con pergamino de retroceso: pila de acciones inversas (tope 5).

Cada accion guarda QUE cambio (no copia total). Al deshacer se revierte la
ultima accion del jugador y TODO su intervalo (lo ocurrido despues de ella
antes de la siguiente accion): acciones enemigas, efectos, reloj, eventos
programados/cancelados, rastro, vida, inventario, puertas y trampas (§2.11).
El tope de 5 se aplica a acciones del jugador (intervalos), no a eventos:
al superar 5 se olvida el intervalo mas viejo completo.
El pergamino se consume (uno del inventario por cada deshacer) y su cantidad
queda excluida de la reversion (§2.11).
"""

from __future__ import annotations

from typing import Any, Iterator

# Ops de accion del jugador: cada una abre un intervalo reversible. Deshacer
# revierte hasta una de estas inclusive (§2.11). "trampa" NO esta aqui: pisar
# una trampa es parte del intervalo de la accion con la que se disparo.
ACCIONES_JUGADOR = {"mover", "abrir", "esperar", "dano_enemigo", "recoger",
                    "soltar", "equipar", "pocion", "antidoto", "antorcha"}


class _NodoPila:
    __slots__ = ("inversa", "siguiente")

    def __init__(self, inversa: dict[str, Any]) -> None:
        self.inversa = inversa
        self.siguiente: _NodoPila | None = None


class PilaDeshacer:
    """Pila propia sobre lista enlazada. Tope 5 intervalos: al llenarse se olvida el mas viejo.

    Un "intervalo" empieza en la accion del jugador y termina justo antes de
    la siguiente; los eventos intermedios (veneno, rearme, turnos enemigos...)
    viven dentro de su intervalo y no gastan tope.
    """

    TOPE = 5

    # a_lista/desde_lista es lo que se guarda en EstadoPartida.pila_deshacer (K2).
    def __init__(self, inversas: list[dict[str, Any]] | None = None) -> None:
        self._cima: _NodoPila | None = None
        self._len = 0
        self._intervalos = 0
        for inv in inversas or []:
            self.apilar(inv)

    def __len__(self) -> int:
        return self._len

    @property
    def vacia(self) -> bool:
        return self._cima is None

    @property
    def intervalos(self) -> int:
        """Acciones del jugador que aun se pueden deshacer."""
        return self._intervalos

    def hay_accion(self) -> bool:
        """True si queda alguna accion del jugador en la pila."""
        return self._intervalos > 0

    def apilar(self, inversa: dict[str, Any]) -> None:
        nodo = _NodoPila(dict(inversa))
        nodo.siguiente = self._cima
        self._cima = nodo
        self._len += 1
        if nodo.inversa.get("op") in ACCIONES_JUGADOR:
            self._intervalos += 1
            if self._intervalos > self.TOPE:
                self._olvidar_mas_vieja()

    def _olvidar_mas_vieja(self) -> None:
        """Descarta la accion mas vieja y todo lo anterior (su intervalo entero)."""
        conservar = self._intervalos - 1
        if conservar <= 0:
            self._cima = None
            self._len = 0
            self._intervalos = 0
            return
        actual = self._cima
        vistos = 0
        encontradas = 0
        while actual is not None:
            vistos += 1
            if actual.inversa.get("op") in ACCIONES_JUGADOR:
                encontradas += 1
                if encontradas == conservar:  # la accion mas vieja que se conserva
                    actual.siguiente = None
                    self._len = vistos
                    self._intervalos = conservar
                    return
            actual = actual.siguiente
        # Defensivo: no habia tantas acciones como decia el contador.
        self._cima = None
        self._len = 0
        self._intervalos = 0

    def desapilar(self) -> dict[str, Any] | None:
        if self._cima is None:
            return None
        inv = self._cima.inversa
        self._cima = self._cima.siguiente
        self._len -= 1
        if inv.get("op") in ACCIONES_JUGADOR:
            self._intervalos -= 1
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


def _reinsertar_turno(agenda, ta: dict[str, Any] | None) -> None:
    """Devuelve a la agenda un turno ya disparado, con su ``(t, seq)`` original."""
    if not ta:
        return
    agenda.reinsertar(int(ta["t"]), str(ta.get("tipo") or "turno"),
                      dict(ta.get("datos") or {}), int(ta["seq"]))


def aplicar_inversa(estado, agenda, inversa: dict[str, Any]) -> bool:
    """Revierte UNA entrada y cancela sus eventos. §2.11: pergaminos excluidos."""
    for seq in (inversa.get("eventos") or []):
        agenda.cancelar_por_seq(seq)
    op = inversa.get("op")
    d = inversa.get("datos") or {}
    # Bloque comun a toda accion del jugador (§2.11/§4.6): reloj, contador
    # de acciones y rastro vuelven al instante anterior a la accion.
    if op in ACCIONES_JUGADOR:
        if "reloj_antes" in d:
            estado.reloj = int(d["reloj_antes"])
        if "acciones_antes" in d:
            estado.acciones_jugador = int(d["acciones_antes"])
        sid = d.get("sala_rastro")
        if sid is not None and "rastro_antes" in d:
            sala_r = estado.salas.get(sid)
            if sala_r is not None:
                sala_r.ultima_visita = d["rastro_antes"]
    if op == "mover":
        # La sala recien despertada vuelve a dormir: sin turno pendiente (ni el
        # de activacion ni los reprogramados durante el intervalo).
        for inst in (d.get("activados") or []):
            agenda.cancelar_donde(
                lambda e, i=inst: e.tipo == "turno" and (e.datos or {}).get("actor") == i)
            for sala in estado.salas.values():
                for e in sala.enemigos:
                    if e.instancia == inst:
                        e.activa = False
                        e.tiempo_siguiente = 0
        destino_id = d.get("sala_destino")
        if destino_id is not None:
            sala_d = estado.salas.get(destino_id)
            if sala_d is not None and "visitada_antes" in d:
                sala_d.visitada = bool(d["visitada_antes"])
            if (not d.get("estaba_visitada", True)
                    and destino_id in estado.salas_visitadas):
                estado.salas_visitadas.remove(destino_id)
        estado.sala_actual = d["origen"]
        if d.get("abrio"):
            s = estado.salas.get(d["sala_puerta"])
            if s and d.get("direccion") in s.salidas:
                s.salidas[d["direccion"]].cerrada = True
        return True
    if op == "esperar":
        return True  # sin estado propio: basta el bloque comun
    if op == "abrir":
        s = estado.salas.get(d.get("sala"))
        if s and d.get("direccion") in s.salidas:
            s.salidas[d["direccion"]].cerrada = True
            if s.salidas[d["direccion"]].destino == estado.sala_salida:
                estado.puerta_salida_abierta = False
        return True
    if op == "dano_enemigo":
        if "derrotados_antes" in d:
            estado.enemigos_derrotados = int(d["derrotados_antes"])
        # Si el golpe letal cancelo el turno pendiente, vuelve tal cual estaba.
        _reinsertar_turno(agenda, d.get("turno_antes"))
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
        # El pulso consumido tambien devuelve duracion al efecto (§4.6).
        for nombre, clave in (("veneno", "veneno_antes"), ("quemadura", "quemadura_antes")):
            if clave in d:
                antes = d[clave]
                if antes is None:
                    estado.jugador.efectos.pop(nombre, None)
                else:
                    estado.jugador.efectos[nombre] = antes
        _reinsertar_turno(agenda, d.get("turno_antes"))
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
        # Mejoras 2026-10: restaurar los efectos que la trampa pudo aplicar.
        for nombre, clave in (("veneno", "veneno_antes"), ("quemadura", "quemadura_antes")):
            antes = d.get(clave)
            if antes is None:
                estado.jugador.efectos.pop(nombre, None)
            else:
                estado.jugador.efectos[nombre] = antes
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
        if inst:
            for sala in estado.salas.values():
                sala.enemigos = [e for e in sala.enemigos if e.instancia != inst]
            agenda.cancelar_donde(lambda ev: (ev.datos or {}).get("actor") == inst)
        # La oleada consumida vuelve a la agenda (su reprogramada ya se cancelo
        # en el preludio generico via "eventos").
        _reinsertar_turno(agenda, d.get("oleada_antes"))
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
                    ta = d.get("turno_antes")
                    if ta is not None:
                        e.tiempo_siguiente = int(ta.get("t", e.tiempo_siguiente))
                        _reinsertar_turno(agenda, ta)
                    return True
        return False
    if op == "turno_enemigo":
        # Turno enemigo que no movio al actor: solo devuelve su programacion.
        inst = d.get("instancia")
        ta = d.get("turno_antes")
        for sala in estado.salas.values():
            for e in sala.enemigos:
                if e.instancia == inst:
                    if ta is not None:
                        e.tiempo_siguiente = int(ta.get("t", e.tiempo_siguiente))
                    break
        _reinsertar_turno(agenda, ta)
        return True
    return False


def deshacer_una(estado, agenda, pila: PilaDeshacer, catalogo: dict | None = None) -> tuple[bool, str]:
    """Usa 1 pergamino: revierte ultima accion jugador + todo su intervalo posterior."""
    if pila.vacia:
        return False, "Nada que deshacer."
    # §2.11: sin ninguna accion en la pila no hay nada que revertir y no se
    # consume pergamino (los eventos sueltos de un intervalo ya olvidado no
    # cuentan: solo se revierte junto a su accion).
    if not pila.hay_accion():
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
        if (inversa.get("op") in ACCIONES_JUGADOR):
            break
    return ok_any, "" if ok_any else "No se pudo revertir."
