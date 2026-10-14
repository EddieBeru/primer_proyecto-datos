"""C1-9 Bitácora para --replay. Solo agrega al final, nunca modifica.

Formato exacto de línea (K3) lo fija C2; aquí las líneas son opacas.
"""

import os

from src.models.errors import BitacoraError


class Bitacora:
    def __init__(self, ruta):
        self.ruta = ruta

    def anotar(self, linea):
        """Agrega una línea al final. Vacía o no-str → ValueError."""
        if not isinstance(linea, str) or not linea.strip():
            raise ValueError(f"línea inválida: {linea!r}")
        try:
            with open(self.ruta, "a", encoding="utf-8") as f:
                f.write(linea.rstrip("\n") + "\n")
        except OSError as e:
            raise BitacoraError(f"no se pudo anotar: {e}") from e

    def leer(self):
        """Retorna líneas en orden. Sin archivo → []. Corrupta → BitacoraError."""
        if not os.path.isfile(self.ruta):
            return []
        try:
            with open(self.ruta, encoding="utf-8") as f:
                return [l.rstrip("\n") for l in f]
        except (OSError, UnicodeDecodeError) as e:
            raise BitacoraError(f"bitácora ilegible: {self.ruta}") from e
