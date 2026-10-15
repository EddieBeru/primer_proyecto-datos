"""Gestor de sprites (Parte 1 §4/§6 + guía §8): dibujante único por id.

PNGs en `assets/sprites/` (ej. el personaje jugable); lo que falte se
dibuja procedural y el id desconocido usa el reemplazo magenta. Se carga
una vez y se reutiliza. 9 clases + 3 comportamientos + puertas.
"""

from __future__ import annotations

import pathlib

import pygame

ASSETS_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "assets" / "sprites"

# Personaje jugable (WASD): 2 frames estilo Pokémon Rojo/Azul.
JUGADOR_PNGS = ["Little Caesars Feliz.png", "Little Caesars Blink.png"]
JUGADOR_ALTO = 48  # el prota es más grande que el mosaico, como en Rojo/Azul

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
        self._jugador_frames: list[pygame.Surface] = self._cargar_jugador()
        self._frame_cache: dict[tuple[int, str], pygame.Surface] = {}
        self._puertas = {
            estado: _mosaico(color, tam=TAM - 8)
            for estado, color in COLORES_PUERTA.items()
        }

    def _cargar_jugador(self) -> list[pygame.Surface]:
        """Frames PNG del prota escalados; vacío si falta el arte (fallback)."""
        frames = []
        for nombre in JUGADOR_PNGS:
            ruta = ASSETS_DIR / nombre
            if not ruta.is_file():
                continue
            try:
                img = pygame.image.load(str(ruta))
            except pygame.error:
                continue
            try:  # sin ventana (tests) no hay formato: usa la imagen tal cual
                img = img.convert_alpha()
            except pygame.error:
                pass
            alto = JUGADOR_ALTO
            ancho = max(1, img.get_width() * alto // max(img.get_height(), 1))
            frames.append(pygame.transform.scale(img, (ancho, alto)))
        return frames

    @property
    def jugador_png(self) -> bool:
        """Hay arte PNG para el personaje (si no, procedural de respaldo)."""
        return len(self._jugador_frames) > 0

    def jugador_frame(self, moviendo: bool, tick: int, facing: str = "S",
                      total: int = 0) -> tuple[pygame.Surface, int]:
        """Frame + salto del prota estilo Pokémon Rojo/Azul.

        Quieto: frame 0, con parpadeo (frame 1 sin salto) cada ~4 s.
        Moviendo: alterna 0/1 cada 2 ticks y el frame 1 salta 3px
        (transformación por offset, sin mutar la imagen). Mirar al Oeste
        espeja (flip) el arte frontal.
        """
        if not self._jugador_frames:
            return self._jugador, 0
        idx, hop = 0, 0
        if moviendo and len(self._jugador_frames) > 1 and (tick // 2) % 2 == 1:
            idx, hop = 1, -3
        elif not moviendo and len(self._jugador_frames) > 1 and total % 240 < 12:
            idx = 1  # parpadeo en reposo, sin salto
        clave = (idx, facing)
        if clave not in self._frame_cache:
            img = self._jugador_frames[idx]
            self._frame_cache[clave] = pygame.transform.flip(img, True, False) \
                if facing == "O" else img
        return self._frame_cache[clave], hop

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
