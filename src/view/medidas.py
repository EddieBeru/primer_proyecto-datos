"""Medidas compartidas: escala de elementos, nunca de la imagen completa."""

from dataclasses import dataclass

import pygame

_FUENTES: dict[tuple[int, bool], pygame.Font] = {}


@dataclass(frozen=True)
class Medidas:
    factor: float = 1.0

    def px(self, valor: float) -> int:
        return round(valor * self.factor)

    def trazo(self, valor: float = 1) -> int:
        return max(1, self.px(valor))

    def fuente(self, tam: int = 16, negrita: bool = False) -> pygame.Font:
        clave = (max(8, self.px(tam)), negrita)
        if clave not in _FUENTES:
            _FUENTES[clave] = pygame.font.SysFont("consolas,monospace", clave[0], bold=negrita)
        return _FUENTES[clave]


def medidas(sup: pygame.Surface) -> Medidas:
    return Medidas(min(sup.get_width() / 1024, sup.get_height() / 800))
