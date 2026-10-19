
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterator


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
    """Eslabon de la lista enlazada. Interno, no se exporta."""

    __slots__ = ("evento", "siguiente")

    def __init__(self, evento: Evento) -> None:
        self.evento = evento
        self.siguiente: _Nodo | None = None


class Agenda:
    """Cola de prioridad ordenada por (t, seq) sobre lista enlazada."""

    # TODO(C2-7): tipos que se programaran aqui: veneno, rearme_trampa, fin_pocion/antorcha.
    # TODO(C2-4/C2-8): tipos cierre_puerta y turno_enemigo ya previstos; turnos los crea RelojVirtual.
    # TODO(C2-9): cada programar() debe guardar su seq para que el deshacer lo cancele.
    def __init__(self) -> None:
        self._cabeza: _Nodo | None = None
        self._seq: int = 0  # proximo numero de secuencia
        self._len: int = 0

    def __len__(self) -> int:
        return self._len

    @property
    def vacia(self) -> bool:
        return self._cabeza is None

    def _insertar(self, ev: Evento) -> Evento:
        """Inserta ordenado por (t, seq) sin tocar el contador de secuencias."""
        nodo = _Nodo(ev)
        # Insercion ordenada: avanza mientras (t, seq) del nodo actual <= nuevo.
        # Como seq siempre crece, basta comparar t y luego seq.
        if self._cabeza is None or (ev.t, ev.seq) < (self._cabeza.evento.t, self._cabeza.evento.seq):
            nodo.siguiente = self._cabeza
            self._cabeza = nodo
        else:
            actual = self._cabeza
            while (
                actual.siguiente is not None
                and (actual.siguiente.evento.t, actual.siguiente.evento.seq) <= (ev.t, ev.seq)
            ):
                actual = actual.siguiente
            nodo.siguiente = actual.siguiente
            actual.siguiente = nodo
        self._len += 1
        return ev

    def programar(self, t: int, tipo: str, datos: dict[str, Any] | None = None) -> Evento:
        """Inserta ordenado y devuelve el evento (ya con seq)."""
        ev = Evento(t=t, tipo=tipo, datos=dict(datos or {}), seq=self._seq)
        self._seq += 1
        return self._insertar(ev)

    def reinsertar(self, t: int, tipo: str, datos: dict[str, Any] | None = None,
                   seq: int = -1) -> Evento:
        """Reinserta un evento ya disparado conservando su ``(t, seq)`` (C2-9).

        Lo usa el deshacer para devolver a la agenda los turnos enemigos que
        el intervalo revertido consumio: el replay vuelve a ver los mismos
        eventos. No reasigna seq (los seq se asignan una sola vez) y si ese
        seq ya estuviera en la agenda devuelve el existente sin duplicar.
        """
        for actual in self:
            if actual.seq == seq:
                return actual
        return self._insertar(Evento(t=t, tipo=tipo, datos=dict(datos or {}), seq=seq))

    def ver_proximo(self) -> Evento | None:
        """Mira sin sacar. None si vacia."""
        return self._cabeza.evento if self._cabeza else None

    def sacar_proximo(self) -> Evento | None:
        """Saca el de menor (t, seq). None si vacia."""
        if self._cabeza is None:
            return None
        ev = self._cabeza.evento
        self._cabeza = self._cabeza.siguiente
        self._len -= 1
        return ev

    def cancelar_por_seq(self, seq: int) -> bool:
        """Quita un evento exacto (lo usa el deshacer C2-9). True si lo hallo."""
        anterior: _Nodo | None = None
        actual = self._cabeza
        while actual is not None:
            if actual.evento.seq == seq:
                if anterior is None:
                    self._cabeza = actual.siguiente
                else:
                    anterior.siguiente = actual.siguiente
                self._len -= 1
                return True
            anterior, actual = actual, actual.siguiente
        return False

    def cancelar_donde(self, pred: Callable[[Evento], bool]) -> int:
        """Quita todos los que cumplan pred(evento). Devuelve cuantos quito.

        Ej: antidoto -> ``agenda.cancelar_donde(lambda e: e.tipo=="veneno")``.
        Deshacer -> pred que filtre por seqs creados por la accion.
        """
        n = 0
        anterior: _Nodo | None = None
        actual = self._cabeza
        while actual is not None:
            if pred(actual.evento):
                if anterior is None:
                    self._cabeza = actual.siguiente
                    actual = self._cabeza
                else:
                    anterior.siguiente = actual.siguiente
                    actual = anterior.siguiente
                self._len -= 1
                n += 1
            else:
                anterior, actual = actual, actual.siguiente
        return n

    def __iter__(self) -> Iterator[Evento]:
        actual = self._cabeza
        while actual is not None:
            yield actual.evento
            actual = actual.siguiente

    # -- K2: la agenda se guarda como list[dict] dentro de EstadoPartida --
    # TODO(C1-8): C1 escribe/lee esta lista a bytes; no cambiar sus claves sin regla 6.3.
    def a_lista(self) -> list[dict[str, Any]]:
        return [e.a_dict() for e in self]

    @classmethod
    def desde_lista(cls, items: list[dict[str, Any]]) -> "Agenda":
        """Reconstruye conservando seqs (para que el determinismo siga)."""
        # TODO(C1-11): cuando el mergesort propio exista, usarlo aqui en vez de sorted().
        ag = cls()
        max_seq = -1
        # items ya vienen ordenados por (t, seq) desde a_lista; se reenlazan
        # en orden sin reasignar seq para no romper el replay.
        anterior: _Nodo | None = None
        for d in sorted(items, key=lambda x: (x["t"], x["seq"])):
            ev = Evento.desde_dict(d)
            max_seq = max(max_seq, ev.seq)
            nodo = _Nodo(ev)
            if anterior is None:
                ag._cabeza = nodo
            else:
                anterior.siguiente = nodo
            anterior = nodo
            ag._len += 1
        ag._seq = max_seq + 1
        return ag
