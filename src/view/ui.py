"""Capa 4: interfaz (Parte 1 §3 + guía §3): vida, stats, inventario, mensajes.

Solo lectura de la foto. `presupuesto` solo se dibuja en modo desarrollo
(F1); nunca para el jugador normal (guía §12: error típico).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.view.sprites import TAM, SpriteManager

if TYPE_CHECKING:  # solo tipos: en runtime la vista solo importa Sesion
    from src.controller2.fachada import FotoEstado

BLANCO = (230, 230, 230)
GRIS = (150, 150, 150)
ROJO = (200, 60, 60)
VERDE = (0, 180, 0)
DORADO = (230, 200, 80)


def dibujar_barra_vida(sup: pygame.Surface, x: int, y: int, w: int,
                       foto: "FotoEstado") -> None:
    """Barra de vida: actual contra máxima (Parte 1 §3)."""
    vida = int(foto.jugador.get("vida", 0))
    maxima = max(int(foto.jugador.get("vida_max", 1)), 1)
    pygame.draw.rect(sup, (60, 0, 0), pygame.Rect(x, y, w, 14))
    pygame.draw.rect(sup, VERDE,
                     pygame.Rect(x, y, w * max(min(vida, maxima), 0) // maxima, 14))


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
    for linea in lineas:
        sup.blit(fuente.render(linea, True, BLANCO), (x, y))
        y += 20
    return y


def dibujar_inventario(sup: pygame.Surface, fuente: pygame.Font, x: int, y: int,
                       foto: "FotoEstado", sprites: SpriteManager,
                       sel_inv: int = 0) -> int:
    """Inventario en orden real; [0] = equipado resaltado (Parte 1 §3)."""
    sup.blit(fuente.render("Mochila (Tab, Enter=equipar, R=usar, Q=soltar):",
                           True, DORADO), (x, y))
    y += 22
    inv = list(foto.inventario or [])
    if not inv:
        sup.blit(fuente.render("(vacía)", True, GRIS), (x, y))
        return y + 20
    for i, item_id in enumerate(inv):
        sup.blit(sprites.sprite(item_id), (x, y))
        marca = " [E]" if i == 0 else ""
        color = DORADO if i == 0 else BLANCO
        sup.blit(fuente.render(f"{item_id}{marca}", True, color), (x + TAM + 6, y + 8))
        if i == sel_inv % len(inv):
            pygame.draw.rect(sup, BLANCO, pygame.Rect(x, y, TAM, TAM), 2)
        y += TAM + 4
    return y


def dibujar_mensajes(sup: pygame.Surface, fuente: pygame.Font, x: int, y: int,
                     foto: "FotoEstado", max_lineas: int = 5) -> None:
    """Panel con las últimas 4-5 líneas de bitácora tal cual (guía §3)."""
    for linea in (foto.mensajes or [])[-max_lineas:]:
        sup.blit(fuente.render(linea, True, GRIS), (x, y))
        y += 18


def dibujar_toast(sup: pygame.Surface, fuente: pygame.Font, texto: str) -> None:
    """Error amable (guía §6): toast abajo; la partida sigue."""
    if not texto:
        return
    etiqueta = fuente.render(texto, True, (255, 255, 255))
    fondo = pygame.Rect(10, sup.get_height() - 34, etiqueta.get_width() + 16, 26)
    pygame.draw.rect(sup, ROJO, fondo)
    sup.blit(etiqueta, (fondo.x + 8, fondo.y + 4))
