"""Sonidos de la vista (guiño: jingle al empezar la partida).

Tolerante a fallos como los sprites: sin audio, sin dispositivo (headless)
o sin códec MP3, la vista sigue jugando en silencio; nunca crashea.
"""

from __future__ import annotations

import pathlib

import pygame

ASSETS_SFX = pathlib.Path(__file__).resolve().parents[2] / "assets" / "sfx"

# Guiño a la empresa que inspiró los visuales del juego: suena al comenzar
# una partida (nueva o cargada).
JINGLE_INICIO = "little_caesars_pizza.mp3"

# El MP3 viene masterizado fuerte: pygame mide amplitud lineal (0.5 ≈ -6 dB,
# apenas audible el cambio), así que va a x0.25 (≈ -12 dB) para no tapar el mix.
VOLUMEN = 0.25


class Sonidos:
    """Carga perezosa y reproducción tolerante a fallos (§12: solo pygame)."""

    def __init__(self) -> None:
        self.disponible = False
        self._jingle: pygame.mixer.Sound | None = None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.disponible = True
        except pygame.error:
            self.disponible = False

    def jingle_inicio(self) -> bool:
        """Suena al empezar la partida. True si sonó de verdad."""
        if not self.disponible:
            return False
        try:
            if self._jingle is None:
                self._jingle = pygame.mixer.Sound(str(ASSETS_SFX / JINGLE_INICIO))
                self._jingle.set_volume(VOLUMEN)
            self._jingle.play()
            return True
        except (pygame.error, FileNotFoundError, OSError):
            return False
