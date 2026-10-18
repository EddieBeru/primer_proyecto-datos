"""Capa 4: interfaz (Parte 1 §3 + guía §3): vida, stats, inventario, mensajes.

Solo lectura de la foto. `presupuesto` solo se dibuja en modo desarrollo
(F1); nunca para el jugador normal (guía §12: error típico).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.view import paleta
from src.view import texto as _texto
from src.view.sprites import TAM, SpriteManager

if TYPE_CHECKING:  # solo tipos: en runtime la vista solo importa Sesion
    from src.controller2.fachada import FotoEstado

BLANCO = paleta.TEXTO
GRIS = paleta.SECUNDARIO
ROJO = paleta.PELIGRO
VERDE = paleta.VIDA
DORADO = paleta.TITULO


def dibujar_barra_vida(sup: pygame.Surface, x: int, y: int, w: int,
                       foto: "FotoEstado") -> None:
    """Barra de vida: actual contra máxima (Parte 1 §3)."""
    vida = int(foto.jugador.get("vida", 0))
    maxima = max(int(foto.jugador.get("vida_max", 1)), 1)
    pygame.draw.rect(sup, paleta.VIDA_FONDO, pygame.Rect(x, y, w, 14))
    pygame.draw.rect(sup, VERDE,
                     pygame.Rect(x, y, w * max(min(vida, maxima), 0) // maxima, 14))


def _ancho_panel(sup: pygame.Surface, x: int) -> int:
    """Ancho disponible desde x hasta el borde derecho."""
    return max(sup.get_width() - x - 8, 100)


def dibujar_stats(sup: pygame.Surface, fuente: pygame.Font, x: int, y: int,
                  foto: "FotoEstado", dev: bool = False) -> int:
    """Estadísticas + efectos + (solo dev) presupuesto. Retorna y final."""
    j = foto.jugador
    lineas = [
        f"Vida {j.get('vida', '?')}/{j.get('vida_max', '?')}",
        f"ATK {j.get('ataque', '?')} DEF {j.get('defensa', '?')} VEL {j.get('velocidad', '?')}",
    ]
    for nombre, restante in (j.get("efectos", {}) or {}).items():
        lineas.append(f"* {nombre}: {restante}")
    lineas.append(f"Pergaminos: {foto.pergaminos} (U)")
    if dev:
        lineas.append(f"[dev] solicitudes: {foto.presupuesto}")
    ancho = _ancho_panel(sup, x)
    for linea in lineas:
        for parte in _texto.envolver(linea, fuente, ancho, 99):
            sup.blit(fuente.render(parte, True, BLANCO), (x, y))
            y += 20
    return y


def dibujar_inventario(sup: pygame.Surface, fuente: pygame.Font, x: int, y: int,
                       foto: "FotoEstado", sprites: SpriteManager,
                       sel_inv: int = 0) -> int:
    """Inventario en orden real; [0] = equipado resaltado (Parte 1 §3)."""
    ancho = _ancho_panel(sup, x)
    for parte in _texto.envolver("Mochila (Tab, Enter=equipar, R=usar, Q=soltar):",
                                 fuente, ancho, 2):
        sup.blit(fuente.render(parte, True, DORADO), (x, y))
        y += 22
    inv = list(foto.inventario or [])
    if not inv:
        sup.blit(fuente.render("(vacía)", True, GRIS), (x, y))
        return y + 20
    texto_w = max(_ancho_panel(sup, x) - (TAM + 6), 60)
    for i, item_id in enumerate(inv):
        marca = " [E]" if i == 0 else ""
        color = DORADO if i == 0 else BLANCO
        partes = _texto.envolver(f"{_texto.etiqueta_item(item_id)}{marca}",
                                 fuente, texto_w, 3)
        alto = max(TAM, len(partes) * 20)
        sup.blit(sprites.sprite(item_id), (x, y))
        for k, parte in enumerate(partes):
            sup.blit(fuente.render(parte, True, color), (x + TAM + 6, y + 8 + k * 20))
        if i == sel_inv % len(inv):
            pygame.draw.rect(sup, DORADO, pygame.Rect(x, y, TAM, TAM), 2)
        y += alto + 6
    return y


def dibujar_mensajes(sup: pygame.Surface, fuente: pygame.Font, x: int, y: int,
                     foto: "FotoEstado", max_lineas: int = 5,
                     ancho_max: int | None = None) -> None:
    """Panel con las últimas líneas de bitácora, humanizadas al jugador."""
    ancho = ancho_max if ancho_max is not None else max(sup.get_width() - x - 10, 100)
    usadas = 0
    for linea in (foto.mensajes or [])[-max_lineas:]:
        if usadas >= max_lineas:
            return
        for parte in _texto.envolver(_texto.humanizar(linea), fuente, ancho,
                                     max_lineas - usadas):
            if usadas >= max_lineas:
                return
            sup.blit(fuente.render(parte, True, GRIS), (x, y))
            y += 18
            usadas += 1


def dibujar_toast(sup: pygame.Surface, fuente: pygame.Font, texto: str) -> None:
    """Error amable (guía §6): toast abajo ajustado a 2 líneas; sigue."""
    if not texto:
        return
    lineas = _texto.envolver(texto, fuente, sup.get_width() - 36, 2)
    etiquetas = [fuente.render(parte, True, paleta.TEXTO_CLARO) for parte in lineas]
    alto = len(etiquetas) * 22 + 4
    fondo = pygame.Rect(10, sup.get_height() - 10 - alto,
                        max(e.get_width() for e in etiquetas) + 16, alto)
    pygame.draw.rect(sup, ROJO, fondo)
    for i, etiqueta in enumerate(etiquetas):
        sup.blit(etiqueta, (fondo.x + 8, fondo.y + 2 + i * 22))
