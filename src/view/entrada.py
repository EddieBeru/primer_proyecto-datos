"""Entrada del jugador: teclado -> intenciones (Parte 1 §5 + guía §5/§10).

Solo traduce. No decide reglas ni toca el estado: recibe la última foto y el
contexto local (hacia dónde mira, qué hay seleccionado) y devuelve el string
para `ses.paso(texto)` o una acción local de UI ("pausa", "tab", ...).
"""

from __future__ import annotations

import pygame

# Tecla -> movimiento (WASD + flechas). "O" es Oeste.
MOVER = {
    pygame.K_w: "n", pygame.K_UP: "n",
    pygame.K_s: "s", pygame.K_DOWN: "s",
    pygame.K_d: "e", pygame.K_RIGHT: "e",
    pygame.K_a: "o", pygame.K_LEFT: "o",
}

OPUESTA = {"n": "s", "s": "n", "e": "o", "o": "e"}


def mover_para_tecla(key: int) -> str | None:
    """Dirección N/S/E/O para la tecla, o None si no es movimiento."""
    return MOVER.get(key)


def intencion_para_tecla(key: int, foto, facing: str,
                         sel_enemigo: int = 0, sel_suelo: int = 0,
                         sel_inv: int = 0) -> str | None:
    """Traduce una tecla a intención `ses.paso()` o acción local.

    Movimiento (WASD/flechas), Espacio (atacar) y F (recoger) los resuelve
    el App por proximidad (`_paso_libre`, `atacar_cercano`, `recoger_cercano`);
    aquí solo van intenciones sin posición. Retorna texto de intención o
    acción local "@...". `None` = tecla sin uso.
    """
    direccion = MOVER.get(key)
    if direccion is not None:
        return "@paso"
    if key == pygame.K_e:
        return f"abrir {facing}"
    if key == pygame.K_r:
        inv = list(foto.inventario or [])
        if not inv:
            return None
        return f"usar {inv[sel_inv % len(inv)]}"
    if key == pygame.K_RETURN or key == pygame.K_KP_ENTER:
        inv = list(foto.inventario or [])
        if not inv:
            return None
        return f"equipar {inv[sel_inv % len(inv)]}"
    if key == pygame.K_q:
        inv = list(foto.inventario or [])
        if not inv:
            return None
        return f"soltar {inv[sel_inv % len(inv)]}"
    if key == pygame.K_u:
        return "deshacer"
    if key == pygame.K_TAB:
        return "@tab-inv"
    if key == pygame.K_t:
        return "@tab-suelo"
    if key == pygame.K_F1:
        return "@dev"
    if key == pygame.K_g:
        return "@guardar"
    if key == pygame.K_ESCAPE:
        return "@pausa"
    return None
