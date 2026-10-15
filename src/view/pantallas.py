"""Pantallas 1.1-1.7 (Parte 1 §1 + guía §9): menú, selección, carga, juego,
fin, error amable y versión incompatible. Cada una dibuja desde datos que le
pasa el App (nunca tocan Sesión directamente, salvo juego vía callbacks).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.view import capas
from src.view import paleta
from src.view import texto as _texto
from src.view import ui
from src.view.sprites import SpriteManager

if TYPE_CHECKING:  # solo tipos: en runtime la vista solo importa Sesion
    from src.controller2.fachada import FotoEstado

BLANCO = paleta.TEXTO
GRIS = paleta.SECUNDARIO
DORADO = paleta.TITULO
FONDO = paleta.FONDO_APP


def _titulo(sup: pygame.Surface, fuente: pygame.Font, texto: str, y: int = 60) -> int:
    etiqueta = fuente.render(texto, True, DORADO)
    sup.blit(etiqueta, (sup.get_width() // 2 - etiqueta.get_width() // 2, y))
    return y + 50


def pantalla_inicio(sup: pygame.Surface, fuente: pygame.Font,
                    puede_continuar: bool) -> None:
    """1.1 Menú: Jugar / Continuar (solo si hay guardado) / Salir."""
    sup.fill(FONDO)
    y = _titulo(sup, fuente, "CRIPTA")
    opciones = ["1 - Jugar"]
    opciones.append("2 - Continuar partida" + ("" if puede_continuar else " (sin guardado)"))
    opciones.append("3 - Salir")
    for opcion in opciones:
        sup.blit(fuente.render(opcion, True, BLANCO),
                 (sup.get_width() // 2 - 130, y))
        y += 30


def pantalla_seleccion(sup: pygame.Surface, fuente: pygame.Font,
                       criptas: list) -> None:
    """1.2 Tarjetas: nombre, salas y dificultad (vienen de main, no del API)."""
    sup.fill(FONDO)
    y = _titulo(sup, fuente, "Elige cripta")
    for i, cripta in enumerate(criptas):
        texto = f"{i + 1} - {cripta.get('nombre', cripta.get('id', '?'))} " \
                f"({cripta.get('salas', '?')} salas, dif. {cripta.get('dificultad', '?')})"
        sup.blit(fuente.render(texto, True, BLANCO),
                 (sup.get_width() // 2 - 220, y))
        y += 30


def pantalla_carga(sup: pygame.Surface, fuente: pygame.Font,
                   detalle: str = "Preparando la cripta…") -> None:
    """1.3 Carga + aviso 429 («esperando N s…», guía §5: sin congelar)."""
    sup.fill(FONDO)
    _titulo(sup, fuente, detalle)


def pantalla_juego(sup: pygame.Surface, fuente: pygame.Font, foto: "FotoEstado",
                   sprites: SpriteManager, area_sala: pygame.Rect,
                   sel_enemigo: int = 0, sel_suelo: int = 0, sel_inv: int = 0,
                   ref_vida: dict | None = None, dev: bool = False,
                   facing: str = "N", desplaza: tuple[int, int] = (0, 0),
                   paso_jugador: tuple[bool, int, int] = (False, 0, 0),
                   pos_jugador: tuple[float, float] | None = None) -> None:
    """1.4 Sala + actores + HUD. Toda la lectura sale de la foto."""
    sup.fill(FONDO)
    titulo = fuente.render(f"Sala {foto.sala_id}: {foto.sala_nombre} [{foto.estado}]",
                           True, DORADO)
    sup.blit(titulo, (10, 8))
    pygame.draw.line(sup, DORADO, (10, 30),
                     (sup.get_width() - 10, 30), 2)
    capas.dibujar_fondo(sup, area_sala, foto, sprites)
    capas.dibujar_estatica(sup, area_sala, foto, sprites, sel_suelo, fuente)
    capas.dibujar_actores(sup, area_sala, foto, sprites, fuente,
                          sel_enemigo, ref_vida, facing, desplaza, paso_jugador,
                          pos_jugador)
    barra_x = area_sala.right + 12
    panel = pygame.Rect(barra_x - 6, 34, sup.get_width() - (barra_x - 6) - 8,
                        sup.get_height() - 34 - 8)
    sup.fill(paleta.PANEL, panel)
    pygame.draw.line(sup, DORADO, (panel.x, panel.y),
                     (panel.x, panel.bottom), 2)
    ui.dibujar_barra_vida(sup, barra_x, 40, min(180, panel.w - 6), foto)
    y = ui.dibujar_stats(sup, fuente, barra_x, 62, foto, dev)
    ui.dibujar_inventario(sup, fuente, barra_x, y + 8, foto, sprites, sel_inv)
    fondo_msg = pygame.Rect(10, sup.get_height() - 152, area_sala.width,
                            144)
    sup.fill(paleta.PANEL, fondo_msg)
    pygame.draw.line(sup, DORADO, (fondo_msg.x, fondo_msg.y),
                     (fondo_msg.right, fondo_msg.y), 2)
    ui.dibujar_mensajes(sup, fuente, 14, sup.get_height() - 148, foto,
                        ancho_max=area_sala.width - 12)
    ui.dibujar_toast(sup, fuente, foto.error or "")


def pantalla_fin(sup: pygame.Surface, fuente: pygame.Font, foto: "FotoEstado",
                 reporte: dict | None = None) -> None:
    """1.5 Victoria / derrota + puntaje + reporte red (guía §9)."""
    sup.fill(FONDO)
    _titulo(sup, fuente, "¡VICTORIA!" if foto.estado == "victoria" else "DERROTA")
    y = 140
    for linea in (foto.mensajes or [])[-3:]:
        sup.blit(fuente.render(linea, True, GRIS), (80, y))
        y += 24
    if reporte and reporte.get("terminada"):
        red = reporte.get("red", {})
        y += 8
        sup.blit(fuente.render(f"puntajes: {reporte.get('puntajes_ruta', '')}",
                               True, BLANCO), (80, y))
        y += 24
        sup.blit(fuente.render(f"red: {red}", True, GRIS), (80, y))


def pantalla_error(sup: pygame.Surface, fuente: pygame.Font, mensaje: str) -> None:
    """1.6 Error amable a pantalla completa (red, presupuesto, guardado)."""
    sup.fill(paleta.PELIGRO_FONDO)
    etiqueta = fuente.render("Algo salió mal (la partida sigue a salvo)",
                             True, paleta.TEXTO_CLARO)
    sup.blit(etiqueta, (sup.get_width() // 2 - etiqueta.get_width() // 2, 60))
    y = 140
    for parte in _texto.envolver(mensaje, fuente, sup.get_width() - 120, 4):
        sup.blit(fuente.render(parte, True, paleta.TEXTO_CLARO), (60, y))
        y += 24
    sup.blit(fuente.render("Pulsa Esc para volver", True, paleta.TEXTO_CLARO),
             (60, y + 8))


def pantalla_version(sup: pygame.Surface, fuente: pygame.Font, mensaje: str) -> None:
    """1.7 Partida de versión anterior: nunca cargar a medias (guía §9)."""
    sup.fill(paleta.MURO)
    etiqueta = fuente.render("Versión anterior", True, paleta.TEXTO_CLARO)
    sup.blit(etiqueta, (sup.get_width() // 2 - etiqueta.get_width() // 2, 60))
    y = 140
    for parte in _texto.envolver(mensaje, fuente, sup.get_width() - 120, 4):
        sup.blit(fuente.render(parte, True, paleta.TEXTO_CLARO), (60, y))
        y += 24
    sup.blit(fuente.render("Pulsa Esc para volver", True, paleta.TEXTO_CLARO),
             (60, y + 8))


def menu_pausa(sup: pygame.Surface, fuente: pygame.Font) -> None:
    """Pausa (Esc): menú local; guardar/cargar/salir vía Sesión en el App."""
    sup.fill(FONDO)
    y = _titulo(sup, fuente, "Pausa")
    for opcion in ["G - Guardar", "C - Cargar", "Esc - Volver", "Q - Salir al menú"]:
        sup.blit(fuente.render(opcion, True, BLANCO),
                 (sup.get_width() // 2 - 110, y))
        y += 30
