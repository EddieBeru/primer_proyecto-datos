"""Ventana nativa, sin resolución intermedia ni escalado del frame."""

from __future__ import annotations

import pygame

RESOLUCIONES = ((1024, 800), (1280, 720), (1600, 900), (1920, 1080))


class Display:
    """Dibuja directamente sobre la superficie de salida, píxel por píxel."""

    def __init__(self, tamano: tuple[int, int], completa: bool = False,
                 superficie: pygame.Surface | None = None) -> None:
        self.externa = superficie is not None
        self.tamano_ventana = tamano
        self.completa = completa
        self.salida = superficie
        if self.externa:
            self.lienzo = superficie
            self.destino = superficie.get_rect()
        else:
            self.cambiar(tamano, completa)

    def cambiar(self, tamano: tuple[int, int], completa: bool) -> None:
        """Recrea la salida; una superficie inyectada nunca abre ventanas."""
        tamano = (max(640, tamano[0]), max(480, tamano[1]))
        if self.externa:
            self.salida = pygame.Surface(tamano)
        else:
            if completa:
                salida = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            else:
                escritorio = pygame.display.get_desktop_sizes()[0]
                escala = min(1, escritorio[0] / tamano[0], escritorio[1] / tamano[1])
                tamano = (round(tamano[0] * escala), round(tamano[1] * escala))
                salida = pygame.display.set_mode(tamano, pygame.RESIZABLE)
            self.salida = salida
        self.completa = completa
        if not completa:
            self.tamano_ventana = self.salida.get_size()
        self._ajustar_lienzo()

    def redimensionar(self, tamano: tuple[int, int]) -> None:
        if min(tamano) <= 0:
            return
        if not self.completa:
            if self.salida.get_size() == tamano:
                self.tamano_ventana = tamano
                self._ajustar_lienzo()
            else:
                self.cambiar(tamano, False)

    def _ajustar_lienzo(self) -> None:
        self.lienzo = self.salida
        self.destino = self.salida.get_rect()

    def coordenadas(self, pos: tuple[int, int]) -> tuple[int, int] | None:
        if not self.destino.collidepoint(pos):
            return None
        return pos

    def presentar(self) -> None:
        if self.externa:
            return
        pygame.display.flip()
