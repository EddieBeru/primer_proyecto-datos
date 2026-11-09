"""Heap binario mínimo propio; empates resueltos por orden de inserción."""

from __future__ import annotations

from typing import Generic, TypeVar

T = TypeVar("T")
Prioridad = int | tuple[int, ...]


class MonticuloMinimo(Generic[T]):
    """Inserción/extracción O(log n), almacenamiento O(n).

    Las prioridades de una instancia deben ser comparables entre sí. Una
    secuencia única evita comparar los valores, incluso si la prioridad empata.
    """

    def __init__(self) -> None:
        self._datos: list[tuple[Prioridad, int, T]] = []
        self._secuencia = 0

    def __len__(self) -> int:
        return len(self._datos)

    def insertar(self, prioridad: Prioridad, valor: T) -> None:
        entrada = (prioridad, self._secuencia, valor)
        self._secuencia += 1
        self._datos.append(entrada)
        indice = len(self._datos) - 1
        while indice:
            padre = (indice - 1) // 2
            if self._datos[padre] <= entrada:
                break
            self._datos[indice] = self._datos[padre]
            indice = padre
        self._datos[indice] = entrada

    def extraer(self) -> T:
        if not self._datos:
            raise IndexError("montículo vacío")
        minimo = self._datos[0]
        ultimo = self._datos.pop()
        if self._datos:
            indice = 0
            while 2 * indice + 1 < len(self._datos):
                hijo = 2 * indice + 1
                if hijo + 1 < len(self._datos) and self._datos[hijo + 1] < self._datos[hijo]:
                    hijo += 1
                if ultimo <= self._datos[hijo]:
                    break
                self._datos[indice] = self._datos[hijo]
                indice = hijo
            self._datos[indice] = ultimo
        return minimo[2]
