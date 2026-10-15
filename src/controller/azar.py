"""Azar reproducible del modelo (§2.6).

Toda aleatoriedad usa una instancia propia ``random.Random(semilla)``.
Nunca el generador global. La semilla se fija al comenzar la partida y se
guarda en el archivo de partida y en la bitácora (§4.11).
"""

from __future__ import annotations

import random


class Azar:
    """Contador de llamadas para verificar determinismo en tests."""

    def __init__(self, semilla: int = 0) -> None:
        self.semilla = int(semilla)
        self._rng = random.Random(self.semilla)
        self.llamadas = 0

    def randint(self, a: int, b: int) -> int:
        self.llamadas += 1
        return self._rng.randint(a, b)

    def choice(self, seq):
        seq = list(seq)
        if not seq:
            raise IndexError("choice de secuencia vacía")
        return seq[self.randint(0, len(seq) - 1)]

    def estado(self) -> tuple:
        """Estado serializable del generador (para guardado)."""
        return (self.semilla, self.llamadas, self._rng.getstate())

    @classmethod
    def desde_estado(cls, semilla: int, llamadas: int, rng_state) -> "Azar":
        az = cls(semilla)
        az._rng.setstate(rng_state)
        az.llamadas = int(llamadas)
        return az
