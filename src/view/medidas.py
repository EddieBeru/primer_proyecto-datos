"""Medidas compartidas: escala de elementos, nunca de la imagen completa."""

from dataclasses import dataclass

import pygame
from src.view.tipografia import fuente as fuente_ui

# Retícula lógica compartida; la escala se aplica con Medidas.px.
ESPACIO = 8
MARGEN = 24



@dataclass(frozen=True)
class Medidas:
    factor: float = 1.0

    def px(self, valor: float) -> int:
        return round(valor * self.factor)

    def trazo(self, valor: float = 1) -> int:
        return max(1, self.px(valor))

    def ui_px(self, valor: float) -> int:
        """Las medidas de lectura no se comprimen en ventanas pequeñas."""
        return round(valor * max(1.0, self.factor))

    def fuente(self, tam: int = 16, negrita: bool = False, *, peso=None, rol=None):
        return fuente_ui(tam, negrita, peso=peso, factor=self.factor, rol=rol)

    def estilo(self, rol):
        return self.fuente(rol=rol)


def medidas(sup: pygame.Surface) -> Medidas:
    return Medidas(min(sup.get_width() / 1024, sup.get_height() / 800))
