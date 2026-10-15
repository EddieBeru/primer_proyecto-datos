"""Las cuatro capas de dibujo (Parte 1 §2): fondo, estática, actores.

La UI (4ta capa) vive en `ui.py`. Cada función recibe la foto (solo lectura)
y dibuja sin mutarla. Direcciones N/S/E/O; ausente = muro, no puerta.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.view.sprites import TAM, SpriteManager

if TYPE_CHECKING:  # solo tipos: en runtime la vista solo importa Sesion
    from src.controller2.fachada import FotoEstado

FONDO_SALA = (38, 36, 48)
MURO = (18, 18, 26)

# Posición de cada puerta dentro del área de sala (N arriba, etc.).
POS_PUERTA = {"N": (0.5, 0.0), "S": (0.5, 1.0), "E": (1.0, 0.5), "O": (0.0, 0.5)}

RADIO_PUERTA = 40  # px para cruzar/recibir aviso
RADIO_OBJETO = 56  # px para recoger del suelo
RADIO_ENEMIGO = 80  # px para atacar (generoso: el aviso solo si lejos)


def rect_puerta(area: pygame.Rect, direccion: str) -> pygame.Rect:
    """Rect de la puerta (misma geometría que dibujar_fondo)."""
    fx, fy = POS_PUERTA[direccion]
    x = area.x + int(fx * (area.w - TAM)) + (0 if fx in (0.0, 1.0) else 0)
    y = area.y + int(fy * (area.h - TAM))
    return pygame.Rect(x, y, TAM, TAM)


def pos_suelo(area: pygame.Rect, i: int) -> tuple[int, int]:
    """Centro del i-ésimo objeto del suelo (misma geometría que dibujar)."""
    x = area.x + 12 + (i % 6) * (TAM + 6)
    y = area.y + area.h - 2 * (TAM + 6) + (i // 6) * (TAM + 6)
    return x + TAM // 2, y + TAM // 2


def pos_enemigo(area: pygame.Rect, i: int) -> tuple[int, int]:
    """Centro del slot del i-ésimo enemigo vivo (misma geometría que dibujar)."""
    x = area.x + 20 + (i % 4) * (TAM + 14)
    y = area.y + area.h // 2 - TAM // 2
    return x + TAM // 2, y + TAM // 2


def pos_enemigo_animada(area: pygame.Rect, i: int, total: int) -> tuple[int, int]:
    """Slot + patrullaje visual (solo vista): deriva senoidal ±8px por slot.

    Los guardianes no abandonan su sitio por diseño (C2-8); esto solo les da
    vida visible. Misma función para dibujar y para proximidad.
    """
    import math
    cx, cy = pos_enemigo(area, i)
    fase = total / 18.0 + i * 1.7
    return cx + round(8 * math.sin(fase)), cy + round(6 * math.cos(fase * 0.8))


def dibujar_fondo(sup: pygame.Surface, area: pygame.Rect, foto: "FotoEstado",
                  sprites: SpriteManager) -> None:
    """Capa 1: piso + puertas (inexistente/abierta/cerrada-llave/trabada)."""
    sup.fill(FONDO_SALA, area)
    pygame.draw.rect(sup, MURO, area, 6)
    for direccion, (fx, fy) in POS_PUERTA.items():
        puerta = (foto.puertas or {}).get(direccion)
        rect = rect_puerta(area, direccion)
        x, y = rect.x, rect.y
        if puerta is None:
            pygame.draw.rect(sup, MURO, pygame.Rect(x, y, TAM, TAM))
            continue
        img = sprites.puerta(bool(puerta.get("cerrada")), puerta.get("llave"))
        sup.blit(img, (x, y))
        if puerta.get("cerrada") and puerta.get("llave"):
            pygame.draw.circle(sup, (230, 200, 80), (x + TAM // 2, y + TAM // 2), 5)


def dibujar_estatica(sup: pygame.Surface, area: pygame.Rect, foto: "FotoEstado",
                     sprites: SpriteManager, sel_suelo: int = 0) -> None:
    """Capa 2: objetos del suelo + trampas (armada vs desactivada)."""
    suelo = list(foto.objetos_suelo or [])
    for i, item_id in enumerate(suelo):
        cx, cy = pos_suelo(area, i)
        x, y = cx - TAM // 2, cy - TAM // 2
        sup.blit(sprites.sprite(item_id), (x, y))
        if i == sel_suelo % max(len(suelo), 1):
            pygame.draw.rect(sup, (255, 255, 255), pygame.Rect(x, y, TAM, TAM), 2)
    for j, trampa in enumerate(foto.trampas or []):
        x = area.x + 12 + (j % 6) * (TAM + 6)
        y = area.y + 12 + (j // 6) * (TAM + 6)
        img = sprites.sprite(str(trampa.get("tipo", "trampa")))
        if not trampa.get("armada", True):
            img = img.copy()
            img.fill((60, 60, 60), special_flags=pygame.BLEND_MULT)
        sup.blit(img, (x, y))


def dibujar_actores(sup: pygame.Surface, area: pygame.Rect, foto: "FotoEstado",
                    sprites: SpriteManager, fuente: pygame.Font,
                    sel_enemigo: int = 0, ref_vida: dict | None = None,
                    facing: str = "N", desplaza: tuple[int, int] = (0, 0),
                    paso_jugador: tuple[bool, int, int] = (False, 0, 0),
                    pos_jugador: tuple[float, float] | None = None,
                    golpe: str | None = None,
                    alcance: frozenset = frozenset()) -> None:
    """Capa 3: jugador + enemigos con barra de vida y color por comportamiento.

    `facing` dibuja hacia dónde mira el personaje; `desplaza` es un offset
    visual del paso (solo vista, sin coordenadas en el modelo).
    `paso_jugador=(moviendo, tick, total)` anima frames PNG estilo Rojo/Azul.
    `pos_jugador` = posición libre en px (None = centro, modo consola).
    """
    ref_vida = ref_vida or {}
    moviendo, tick, total = paso_jugador
    img_jugador, hop = sprites.jugador_frame(moviendo, tick, facing, total)
    if pos_jugador is None:
        jx = area.x + area.w // 2 - img_jugador.get_width() // 2 + desplaza[0]
        jy = area.y + area.h // 2 - TAM // 2 + desplaza[1] + hop
    else:
        jx = pos_jugador[0] - img_jugador.get_width() // 2 + desplaza[0]
        jy = pos_jugador[1] - img_jugador.get_height() + TAM // 2 + desplaza[1] + hop
    sup.blit(img_jugador, (jx, jy))
    vivos = [e for e in (foto.enemigos or []) if e.get("vida", 0) > 0]
    for i, enemigo in enumerate(vivos):
        cx, cy = pos_enemigo_animada(area, i, total)
        x, y = cx - TAM // 2, cy - TAM // 2
        sup.blit(sprites.enemigo(str(enemigo.get("comportamiento", ""))), (x, y))
        vida = int(enemigo.get("vida", 0))
        _barra(sup, x, y - 10, TAM, 6, vida, max(ref_vida.get(enemigo.get("instancia", ""), vida), vida, 1))
        etiqueta = fuente.render(f"{i + 1}:{enemigo.get('instancia', '?')} {vida}",
                                  True, (230, 230, 230))
        sup.blit(etiqueta, (x, y + TAM + 2))
        if enemigo.get("instancia") == golpe:
            pygame.draw.rect(sup, (255, 255, 255), pygame.Rect(x - 2, y - 2, TAM + 4, TAM + 4), 3)
        if enemigo.get("instancia") in alcance:
            pygame.draw.rect(sup, (0, 220, 0), pygame.Rect(x - 2, y - 2, TAM + 4, TAM + 4), 2)
        if i == sel_enemigo % max(len(vivos), 1):
            pygame.draw.rect(sup, (255, 255, 0), pygame.Rect(x, y, TAM, TAM), 2)


def _barra(sup: pygame.Surface, x: int, y: int, w: int, h: int,
           vida: int, referencia: int) -> None:
    """Barra proporcional a la primera vida vista (guía §8; K5 no trae máximo)."""
    referencia = max(referencia, 1)
    pygame.draw.rect(sup, (60, 0, 0), pygame.Rect(x, y, w, h))
    pygame.draw.rect(sup, (0, 180, 0),
                     pygame.Rect(x, y, max(0, w * min(vida, referencia) // referencia), h))
