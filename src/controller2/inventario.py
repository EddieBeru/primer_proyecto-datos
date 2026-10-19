
from __future__ import annotations

from typing import Callable, Iterator


class InventarioLlenoError(Exception):
    pass


class _NodoInv:
    __slots__ = ("valor", "anterior", "siguiente")

    def __init__(self, valor: str) -> None:
        self.valor = valor
        self.anterior: _NodoInv | None = None
        self.siguiente: _NodoInv | None = None


class Inventario:
    """Mochila con tope por CANTIDAD (el `peso` del catalogo no limita aca)."""

    # `ordenar` recibe el orden_fn de C1 (C2 no usa sorted); `a_lista` es el
    # orden que se guarda en JugadorVivo.inventario (K2).
    def __init__(self, maximo: int, items: list[str] | None = None) -> None:
        if maximo <= 0:
            raise ValueError("maximo debe ser > 0")
        self.maximo = maximo
        self._cabeza: _NodoInv | None = None
        self._cola: _NodoInv | None = None
        self._len = 0
        for it in items or []:
            self.recoger(it)

    def __len__(self) -> int:
        return self._len

    @property
    def lleno(self) -> bool:
        return self._len >= self.maximo

    @property
    def vacio(self) -> bool:
        return self._len == 0

    def _nodo_en(self, pos: int) -> _NodoInv:
        if not 0 <= pos < self._len:
            raise IndexError("posicion fuera de rango")
        # recorre desde el extremo mas cercano
        if pos < self._len // 2:
            n = self._cabeza
            for _ in range(pos):
                n = n.siguiente  # type: ignore[union-attr]
        else:
            n = self._cola
            for _ in range(self._len - 1 - pos):
                n = n.anterior  # type: ignore[union-attr]
        return n  # type: ignore[return-value]

    def _desenganchar(self, n: _NodoInv) -> str:
        if n.anterior:
            n.anterior.siguiente = n.siguiente
        else:
            self._cabeza = n.siguiente
        if n.siguiente:
            n.siguiente.anterior = n.anterior
        else:
            self._cola = n.anterior
        n.anterior = n.siguiente = None
        self._len -= 1
        return n.valor

    def recoger(self, item_id: str) -> None:
        """Agrega al fondo. Lanza InventarioLlenoError si no cabe."""
        if self.lleno:
            raise InventarioLlenoError(f"Mochila llena ({self.maximo}).")
        n = _NodoInv(item_id)
        if self._cola is None:
            self._cabeza = self._cola = n
        else:
            n.anterior = self._cola
            self._cola.siguiente = n
            self._cola = n
        self._len += 1

    def soltar_en(self, pos: int) -> str:
        """Suelta el de la posicion pos (0=frente). Devuelve su id."""
        return self._desenganchar(self._nodo_en(pos))

    def soltar_id(self, item_id: str) -> str:
        n = self._cabeza
        while n is not None and n.valor != item_id:
            n = n.siguiente
        if n is None:
            raise KeyError(f"{item_id} no esta en el inventario.")
        return self._desenganchar(n)

    def equipar(self, pos: int) -> str:
        """Mueve el de pos al frente (equipar = ir al frente)."""
        if pos == 0:
            return self._cabeza.valor  # type: ignore[union-attr]
        valor = self._desenganchar(self._nodo_en(pos))
        n = _NodoInv(valor)
        n.siguiente = self._cabeza
        if self._cabeza:
            self._cabeza.anterior = n
        self._cabeza = n
        if self._cola is None:
            self._cola = n
        self._len += 1
        return valor

    def contiene(self, item_id: str) -> bool:
        return any(v == item_id for v in self)

    def __iter__(self) -> Iterator[str]:
        n = self._cabeza
        while n is not None:
            yield n.valor
            n = n.siguiente

    def __reversed__(self) -> Iterator[str]:
        n = self._cola
        while n is not None:
            yield n.valor
            n = n.anterior

    def a_lista(self) -> list[str]:
        return list(self)

    def ordenar(self, algoritmo: Callable[[list[str]], list[str]]) -> None:
        """Reordena usando el mergesort de C1-11 (inyectado, no reescrito).

        ``algoritmo``: funcion (lista) -> lista ordenada. C2 no usa
        sort/sorted aqui; si falta, se lanza TypeError en vez de adivinar.
        """
        if algoritmo is None:
            raise TypeError("ordenar necesita el mergesort de C1 (C1-11).")
        ordenados = algoritmo(self.a_lista())
        self._cabeza = self._cola = None
        self._len = 0
        for it in ordenados:
            self.recoger(it)

    @classmethod
    def desde_jugador(cls, inventario: list[str], maximo: int) -> "Inventario":
        return cls(maximo, list(inventario))
