
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterator

from src.controller2.orden_local import insercion


@dataclass
class Evento:
    """Un pendiente. ``seq`` lo asigna la Agenda, no el que programa."""

    t: int
    tipo: str
    datos: dict[str, Any] = field(default_factory=dict)
    seq: int = -1

    def __post_init__(self) -> None:
        if not isinstance(self.t, int) or self.t < 0:
            raise ValueError("t debe ser int >= 0")
        if not self.tipo:
            raise ValueError("tipo no puede ser vacio")

    def a_dict(self) -> dict[str, Any]:
        return {"t": self.t, "seq": self.seq, "tipo": self.tipo, "datos": dict(self.datos)}

    @classmethod
    def desde_dict(cls, d: dict[str, Any]) -> "Evento":
        return cls(t=d["t"], tipo=d["tipo"], datos=dict(d.get("datos") or {}), seq=d["seq"])


class _Nodo:
    """Eslabon doble de la agenda. Interno, no se exporta."""

    __slots__ = ("evento", "anterior", "siguiente", "tipo_ant", "tipo_sig")

    def __init__(self, evento: Evento) -> None:
        self.evento = evento
        self.anterior: _Nodo | None = None
        self.siguiente: _Nodo | None = None
        # enlaces de la lista intrusiva por tipo (índice de cancelación §4.1)
        self.tipo_ant: _Nodo | None = None
        self.tipo_sig: _Nodo | None = None


class _EntradaTipo:
    __slots__ = ("tipo", "cabeza", "cola")

    def __init__(self, tipo: str) -> None:
        self.tipo = tipo
        self.cabeza: _Nodo | None = None
        self.cola: _Nodo | None = None


class _IndiceTipos:
    """Hash encadenado propio tipo -> lista intrusiva (sin dict: §7).

    Permite `cancelar_tipo(tipo)` en O(k) (k = eventos de ese tipo) sin
    recorrer la agenda completa. Cubetas = listas de entradas; el choque se
    resuelve recorriendo la cubeta.
    """

    __slots__ = ("_cubetas",)

    def __init__(self, cubetas: int = 16) -> None:
        self._cubetas: list[list[_EntradaTipo]] = [[] for _ in range(cubetas)]

    @staticmethod
    def _hash(tipo: str) -> int:
        h = 5381
        for ch in tipo:
            h = ((h << 5) + h) ^ ord(ch)
        return h & 0x7FFFFFFF

    def _cubeta(self, tipo: str) -> list[_EntradaTipo]:
        return self._cubetas[self._hash(tipo) % len(self._cubetas)]

    def _entrada(self, tipo: str) -> _EntradaTipo | None:
        for entrada in self._cubeta(tipo):
            if entrada.tipo == tipo:
                return entrada
        return None

    def cabeza(self, tipo: str) -> _Nodo | None:
        entrada = self._entrada(tipo)
        return entrada.cabeza if entrada is not None else None

    def agregar(self, nodo: _Nodo) -> None:
        tipo = nodo.evento.tipo
        entrada = self._entrada(tipo)
        if entrada is None:
            entrada = _EntradaTipo(tipo)
            self._cubeta(tipo).append(entrada)
        nodo.tipo_ant = entrada.cola
        nodo.tipo_sig = None
        if entrada.cola is not None:
            entrada.cola.tipo_sig = nodo
        else:
            entrada.cabeza = nodo
        entrada.cola = nodo

    def quitar(self, nodo: _Nodo) -> None:
        tipo = nodo.evento.tipo
        entrada = self._entrada(tipo)
        if entrada is not None:
            if entrada.cabeza is nodo:
                entrada.cabeza = nodo.tipo_sig
            if entrada.cola is nodo:
                entrada.cola = nodo.tipo_ant
            if entrada.cabeza is None:
                cubeta = self._cubeta(tipo)
                try:
                    cubeta.remove(entrada)
                except ValueError:
                    pass
        if nodo.tipo_ant is not None:
            nodo.tipo_ant.tipo_sig = nodo.tipo_sig
        if nodo.tipo_sig is not None:
            nodo.tipo_sig.tipo_ant = nodo.tipo_ant
        nodo.tipo_ant = nodo.tipo_sig = None


class Agenda:
    """Cola de prioridad ordenada por (t, seq), con índices de cancelación.

    - Lista doble por (t, seq): sacar el próximo es O(1) y quitar un nodo
      dado es O(1).
    - Índice por tipo (hash propio): `cancelar_tipo` O(k), sin barrer todo.
    - Índice por seq (lista directa compactable): `cancelar_por_seq` O(1).
    """

    def __init__(self) -> None:
        self._cabeza: _Nodo | None = None
        self._cola: _Nodo | None = None
        self._seq: int = 0  # proximo numero de secuencia
        self._len: int = 0
        self._tipos = _IndiceTipos()
        self._por_seq: list[_Nodo | None] = []

    def __len__(self) -> int:
        return self._len

    @property
    def vacia(self) -> bool:
        return self._cabeza is None

    # -- alta / baja --
    def programar(self, t: int, tipo: str, datos: dict[str, Any] | None = None) -> Evento:
        """Inserta ordenado por (t, seq) y devuelve el evento."""
        ev = Evento(t=t, tipo=tipo, datos=dict(datos or {}), seq=self._seq)
        self._seq += 1
        nodo = _Nodo(ev)
        cola = self._cola
        if cola is None or (ev.t, ev.seq) >= (cola.evento.t, cola.evento.seq):
            # Camino rápido: el reloj casi siempre avanza -> se agrega al final.
            if cola is None:
                self._cabeza = self._cola = nodo
            else:
                nodo.anterior = cola
                cola.siguiente = nodo
                self._cola = nodo
        else:
            # Busca el primer nodo con clave mayor; inserta justo antes.
            actual = self._cabeza
            while actual is not None and (actual.evento.t, actual.evento.seq) <= (ev.t, ev.seq):
                actual = actual.siguiente
            if actual is None:
                nodo.anterior = self._cola
                if self._cola is not None:
                    self._cola.siguiente = nodo
                self._cola = nodo
            else:
                nodo.siguiente = actual
                nodo.anterior = actual.anterior
                if actual.anterior is not None:
                    actual.anterior.siguiente = nodo
                else:
                    self._cabeza = nodo
                actual.anterior = nodo
        self._len += 1
        self._tipos.agregar(nodo)
        self._registrar_seq(nodo)
        return ev

    def ver_proximo(self) -> Evento | None:
        """Mira sin sacar. None si vacia."""
        return self._cabeza.evento if self._cabeza else None

    def sacar_proximo(self) -> Evento | None:
        """Saca el de menor (t, seq). None si vacia."""
        if self._cabeza is None:
            return None
        ev = self._cabeza.evento
        self._desenlazar(self._cabeza)
        return ev

    def cancelar_por_seq(self, seq: int) -> bool:
        """Quita un evento exacto. O(1) con el índice por seq (§4.1)."""
        if 0 <= seq < len(self._por_seq):
            nodo = self._por_seq[seq]
            if nodo is not None:
                self._desenlazar(nodo)
                return True
        return False

    def cancelar_tipo(self, tipo: str) -> int:
        """Quita todos los eventos de un tipo. O(k), k = eventos del tipo.

        Lo usa el antídoto para el veneno: sin recorrer la agenda entera.
        """
        n = 0
        nodo = self._tipos.cabeza(tipo)
        while nodo is not None:
            siguiente = nodo.tipo_sig  # se captura antes de desenlazar
            self._desenlazar(nodo)
            nodo = siguiente
            n += 1
        return n

    def cancelar_donde(self, pred: Callable[[Evento], bool]) -> int:
        """Quita todos los que cumplan pred(evento). Devuelve cuantos quito.

        Para predicados que no son por tipo ni seq (p. ej. `datos["actor"]`).
        """
        n = 0
        actual = self._cabeza
        while actual is not None:
            siguiente = actual.siguiente
            if pred(actual.evento):
                self._desenlazar(actual)
                n += 1
            actual = siguiente
        return n

    def __iter__(self) -> Iterator[Evento]:
        actual = self._cabeza
        while actual is not None:
            yield actual.evento
            actual = actual.siguiente

    # -- indices internos --
    def _desenlazar(self, nodo: _Nodo) -> None:
        if nodo.anterior is None:
            self._cabeza = nodo.siguiente
        else:
            nodo.anterior.siguiente = nodo.siguiente
        if nodo.siguiente is None:
            self._cola = nodo.anterior
        else:
            nodo.siguiente.anterior = nodo.anterior
        nodo.anterior = nodo.siguiente = None
        self._len -= 1
        seq = nodo.evento.seq
        if 0 <= seq < len(self._por_seq):
            self._por_seq[seq] = None
        self._tipos.quitar(nodo)

    def _registrar_seq(self, nodo: _Nodo) -> None:
        seq = nodo.evento.seq
        if seq >= len(self._por_seq):
            self._por_seq.extend([None] * (seq + 1 - len(self._por_seq)))
        self._por_seq[seq] = nodo
        # Si los seqs viejos ya no viven, compacta para no crecer sin fin.
        if len(self._por_seq) > 4 * self._len + 64:
            self._compactar_seq()

    def _compactar_seq(self) -> None:
        # OJO: iterar `self` devuelve Evento, no _Nodo; aquí se camina la
        # cadena de nodos directamente.
        nueva: list[_Nodo | None] = []
        actual = self._cabeza
        while actual is not None:
            seq = actual.evento.seq
            if seq >= len(nueva):
                nueva.extend([None] * (seq + 1 - len(nueva)))
            nueva[seq] = actual
            actual = actual.siguiente
        self._por_seq = nueva

    # -- K2: la agenda se guarda como list[dict] dentro de EstadoPartida --
    # TODO(C1-8): C1 escribe/lee esta lista a bytes; no cambiar sus claves sin regla 6.3.
    def a_lista(self) -> list[dict[str, Any]]:
        return [e.a_dict() for e in self]

    @classmethod
    def desde_lista(cls, items: list[dict[str, Any]]) -> "Agenda":
        """Reconstruye conservando seqs (para que el determinismo siga)."""
        ag = cls()
        max_seq = -1
        # items ya vienen ordenados por (t, seq) desde a_lista; la inserción
        # local (sin sorted, §4.9) lo garantiza también si llegaran sueltos.
        anterior: _Nodo | None = None
        for d in insercion(items, clave=lambda x: (x["t"], x["seq"])):
            ev = Evento.desde_dict(d)
            max_seq = max(max_seq, ev.seq)
            nodo = _Nodo(ev)
            if anterior is None:
                ag._cabeza = nodo
            else:
                anterior.siguiente = nodo
                nodo.anterior = anterior
            anterior = nodo
            ag._cola = nodo
            ag._len += 1
            ag._tipos.agregar(nodo)
            if ev.seq >= len(ag._por_seq):
                ag._por_seq.extend([None] * (ev.seq + 1 - len(ag._por_seq)))
            ag._por_seq[ev.seq] = nodo
        ag._seq = max_seq + 1
        return ag
