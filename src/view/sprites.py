"""Gestor de sprites (Parte 1 §4/§6 + guía §8): dibujante único por id.

Todo procedural (cuadros de color): sin archivos externos. Se carga una vez
(`SpriteManager()`) y se reutiliza. Id desconocido -> sprite de reemplazo
magenta, cacheado. 9 clases + 3 comportamientos + puertas 4 dir x 4 estados.
"""

from __future__ import annotations

import pygame

TAM = 36  # lado del mosaico base

# 9 clases del catálogo -> color.
COLORES_CLASE = {
    "enemigo": (200, 60, 60),
    "arma": (200, 200, 220),
    "armadura": (120, 140, 180),
    "pocion": (220, 80, 120),
    "antidoto": (120, 220, 140),
    "llave": (230, 200, 80),
    "antorcha": (240, 140, 40),
    "pergamino_retroceso": (200, 160, 240),
    "trampa": (140, 140, 140),
}

# Comportamientos visibles (guía §8).
COLORES_COMPORTAMIENTO = {
    "guardián": (200, 60, 60),
    "errante": (230, 130, 40),
    "rastreador": (150, 80, 200),
}

# Puertas: estado -> color (4 direcciones x 4 estados, Parte 1 §6).
COLORES_PUERTA = {
    "abierta": (120, 200, 120),
    "cerrada-llave": (200, 60, 60),
    "trabada": (110, 110, 110),
}

REEMPLAZO = (255, 0, 255)  # sprite de reemplazo: id sin dibujante
JUGADOR = (70, 130, 230)


def _mosaico(color, tam: int = TAM, borde=(20, 20, 20)) -> pygame.Surface:
    sup = pygame.Surface((tam, tam))
    sup.fill(color)
    pygame.draw.rect(sup, borde, sup.get_rect(), 2)
    return sup


def clase_de_id(item_id: str) -> str:
    """Adivina la clase por el id (solo para elegir color; nada de reglas)."""
    bajo = item_id.lower()
    if "pocion" in bajo:
        return "pocion"
    if "antidoto" in bajo:
        return "antidoto"
    if "llave" in bajo:
        return "llave"
    if "antorcha" in bajo:
        return "antorcha"
    if "pergamino" in bajo:
        return "pergamino_retroceso"
    if "espada" in bajo or "arma" in bajo:
        return "arma"
    if "escudo" in bajo or "armadura" in bajo:
        return "armadura"
    if "pinchos" in bajo or "veneno" in bajo or "trampa" in bajo:
        return "trampa"
    if any(k in bajo for k in ("esqueleto", "murcielago", "sombra", "jefe", "rata", "goblin")):
        return "enemigo"
    return "desconocida"


class SpriteManager:
    """Carga una vez; `sprite(id)` siempre retorna algo (reemplazo si falta)."""

    def __init__(self) -> None:
        self._cache: dict[str, pygame.Surface] = {}
        self._reemplazo = _mosaico(REEMPLAZO)
        self._jugador = _mosaico(JUGADOR)
        self._puertas = {
            estado: _mosaico(color, tam=TAM - 8)
            for estado, color in COLORES_PUERTA.items()
        }

    def sprite(self, item_id: str) -> pygame.Surface:
        if item_id in self._cache:
            return self._cache[item_id]
        clase = clase_de_id(item_id)
        color = COLORES_CLASE.get(clase, REEMPLAZO)
        sup = _mosaico(color)
        if clase == "desconocida":
            sup = self._reemplazo
        self._cache[item_id] = sup
        return sup

    def es_reemplazo(self, item_id: str) -> bool:
        return clase_de_id(item_id) == "desconocida"

    @property
    def reemplazo(self) -> pygame.Surface:
        return self._reemplazo

    @property
    def jugador(self) -> pygame.Surface:
        return self._jugador

    def enemigo(self, comportamiento: str) -> pygame.Surface:
        return _mosaico(COLORES_COMPORTAMIENTO.get(comportamiento, REEMPLAZO))

    def puerta(self, cerrada: bool, llave) -> pygame.Surface | None:
        """Puerta por estado. `None` solo si el llamante pide muro (sin salida)."""
        if not cerrada:
            return self._puertas["abierta"]
        if llave:
            return self._puertas["cerrada-llave"]
        return self._puertas["trabada"]
