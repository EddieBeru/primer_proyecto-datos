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
from src.view.medidas import medidas

if TYPE_CHECKING:  # solo tipos: en runtime la vista solo importa Sesion
    from src.controller2.fachada import FotoEstado

BLANCO = paleta.TEXTO
GRIS = paleta.SECUNDARIO
ROJO = paleta.PELIGRO
VERDE = paleta.VIDA
DORADO = paleta.TITULO
ANCHO_LATERAL = 340


def es_panoramica(sup: pygame.Surface) -> bool:
    m = medidas(sup)
    p = m.px
    return (sup.get_width() >= p(1060) and sup.get_height() >= p(640)
            and sup.get_width() / sup.get_height() >= 1.6)


def dibujar_barra_vida(sup: pygame.Surface, x: int, y: int, w: int,
                       foto: "FotoEstado") -> None:
    """Barra de vida: actual contra máxima (Parte 1 §3)."""
    m = medidas(sup)
    p = m.px
    vida = int(foto.jugador.get("vida", 0))
    maxima = max(int(foto.jugador.get("vida_max", 1)), 1)
    pygame.draw.rect(sup, paleta.VIDA_FONDO, pygame.Rect(x, y, w, p(14)))
    pygame.draw.rect(sup, VERDE,
                     pygame.Rect(x, y, w * max(min(vida, maxima), 0) // maxima, p(14)))


def _ancho_panel(sup: pygame.Surface, x: int) -> int:
    """Ancho disponible desde x hasta el borde derecho."""
    return max(sup.get_width() - x - 8, 100)


def dibujar_stats(sup: pygame.Surface, fuente: pygame.Font, x: int, y: int,
                  foto: "FotoEstado", dev: bool = False) -> int:
    """Estadísticas + efectos + (solo dev) presupuesto. Retorna y final."""
    m = medidas(sup)
    p = m.px
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
            y += p(20)
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


def dibujar_contadores(sup: pygame.Surface, fuente: pygame.Font, rect: pygame.Rect,
                       foto: "FotoEstado", dev: bool = False) -> None:
    """Fila única: vida, stats, efectos y pergaminos (Parte 1 §3)."""
    m = medidas(sup)
    p = m.px
    j = foto.jugador
    x, y = rect.x, rect.y
    etiqueta = fuente.render("Vida", True, GRIS)
    sup.blit(etiqueta, (x, y + p(2)))
    x += etiqueta.get_width() + p(8)
    vida = int(j.get("vida", 0))
    maxima = max(int(j.get("vida_max", 1)), 1)
    ancho = p(150)
    pygame.draw.rect(sup, paleta.VIDA_FONDO, pygame.Rect(x, y + p(3), ancho, p(14)))
    pygame.draw.rect(sup, VERDE, pygame.Rect(
        x, y + p(3), ancho * max(min(vida, maxima), 0) // maxima, p(14)))
    marcador = fuente.render(f"{vida}/{maxima}", True, BLANCO)
    sup.blit(marcador, (x + ancho + p(8), y + p(2)))
    x += ancho + p(8) + marcador.get_width() + p(24)
    stats = fuente.render(
        f"ATK {j.get('ataque', '?')}  DEF {j.get('defensa', '?')}  "
        f"VEL {j.get('velocidad', '?')}", True, BLANCO)
    sup.blit(stats, (x, y + p(2)))
    x += stats.get_width() + p(24)
    perg = fuente.render(f"Pergaminos: {foto.pergaminos}", True, DORADO)
    sup.blit(perg, (x, y + p(2)))
    x += perg.get_width() + p(16)
    for nombre, restante in (j.get("efectos", {}) or {}).items():
        chip = fuente.render(f"* {nombre} {restante}", True, GRIS)
        sup.blit(chip, (x, y + p(2)))
        x += chip.get_width() + p(12)
    if dev:
        aviso = fuente.render(f"[dev] solicitudes: {foto.presupuesto}", True, GRIS)
        sup.blit(aviso, (rect.right - aviso.get_width(), y + p(2)))


def dibujar_mochila(sup: pygame.Surface, fuente: pygame.Font, rect: pygame.Rect,
                    foto: "FotoEstado", sprites: SpriteManager,
                    sel_inv: int = 0, orden: list | None = None,
                    sufijo_orden: str | None = None) -> list:
    """Objetos en fila horizontal; equipado con "E", seleccionado con marco.

    `orden` es la copia ordenada por la Sesión (§4.5): solo cambia el dibujo
    y el mapeo de la selección, jamás el inventario real. Sin `orden` se
    mantiene el orden real ([0] = equipado, marca "E" como siempre).
    """
    m = medidas(sup)
    p = m.px
    etiqueta = fuente.render("Mochila" + (sufijo_orden or ""), True, DORADO)
    sup.blit(etiqueta, (rect.x, rect.y))
    x = rect.x
    y = rect.y + p(24)
    inv = list(orden) if orden is not None else list(foto.inventario or [])
    if not inv:
        sup.blit(fuente.render("Sin objetos todavía", True, GRIS), (x, y + p(12)))
        return []
    equipados = {i for i in (getattr(foto, "arma_equipada", None),
                             getattr(foto, "armadura_equipada", None)) if i}
    lado = sprites.tam + p(4)
    capacidad = max(1, rect.w // (lado + p(8)))
    elegido = sel_inv % len(inv)
    inicio = min(max(0, elegido - capacidad + 1), max(0, len(inv) - capacidad))
    contador = fuente.render(f"{elegido + 1}/{len(inv)}", True, GRIS)
    sup.blit(contador, (rect.right - contador.get_width(), rect.y))
    hotspots = []
    for i in range(inicio, min(inicio + capacidad, len(inv))):
        item_id = inv[i]
        caja = pygame.Rect(x, y, lado, lado)
        sup.fill(paleta.PANEL, caja)
        icono = sprites.sprite(item_id)
        sup.blit(icono, icono.get_rect(center=caja.center))
        pygame.draw.rect(sup, DORADO if i == sel_inv % len(inv) else GRIS,
                         caja, m.trazo(2))
        if item_id in equipados or (orden is None and i == 0):
            sup.blit(fuente.render("E", True, DORADO), (caja.x + p(2), caja.y))
        hotspots.append((caja, ("inventario", i)))
        x += lado + p(8)
    return hotspots


def dibujar_hud(sup: pygame.Surface, fuente: pygame.Font, rect: pygame.Rect,
                 foto: "FotoEstado", sprites: SpriteManager, sel_inv: int,
                 orden: list | None, criterio: str | None, dev: bool,
                 ayudas: bool, raton: tuple[int, int] | None) -> list:
    """Panel adaptable: selección visible y acciones con teclado o ratón."""
    m = medidas(sup)
    p = m.px
    lateral = es_panoramica(sup)
    pygame.draw.rect(sup, paleta.PANEL, rect)
    pygame.draw.rect(sup, (230, 207, 177), rect, m.trazo())
    contenido = rect.inflate(-p(24), -p(20))
    x, y, w = contenido.x, contenido.y, contenido.w
    if lateral:
        sup.blit(fuente.render("EXPLORADOR", True, DORADO), (x, y))
        dibujar_barra_vida(sup, x, y + p(28), w, foto)
        y = dibujar_stats(sup, fuente, x, y + p(52), foto, dev) + p(18)
    else:
        dibujar_contadores(sup, fuente, contenido, foto, dev)
        y += p(30)
    inv = list(orden) if orden is not None else list(foto.inventario or [])
    # En ventana, mochila a la izquierda y acciones a la derecha.
    inv_w = w if lateral else max(p(240), w // 2 - p(18))
    hotspots = dibujar_mochila(
        sup, fuente, pygame.Rect(x, y, inv_w, p(80)), foto, sprites, sel_inv,
        orden=orden, sufijo_orden=f" · {criterio}" if criterio else None)
    nombre = _texto.etiqueta_item(inv[sel_inv % len(inv)]) if inv else "Tab o clic para seleccionar"
    for i, linea in enumerate(_texto.envolver(nombre, fuente, inv_w, 2)):
        sup.blit(fuente.render(linea, True, BLANCO), (x, y + p(82) + p(19) * i))
    ax = x if lateral else x + inv_w + p(24)
    ay = y + p(140) if lateral else y
    aw = w if lateral else w - inv_w - p(24)
    acciones = (("E", "Abrir", pygame.K_e, True),
                ("Espacio", "Atacar", pygame.K_SPACE, True),
                ("F", "Recoger", pygame.K_f, True),
                ("R", "Usar", pygame.K_r, bool(inv)),
                ("Enter", "Equipar", pygame.K_RETURN, bool(inv)),
                ("Q", "Soltar", pygame.K_q, bool(inv)))
    for i, (tecla, etiqueta, key, habilitado) in enumerate(acciones):
        col, fila = i % 2, i // 2
        boton = pygame.Rect(ax + col * (aw // 2 + p(4)), ay + fila * p(36),
                            aw // 2 - p(4), p(30))
        hover = habilitado and raton is not None and boton.collidepoint(raton)
        pygame.draw.rect(sup, (252, 228, 198) if hover else paleta.FONDO_APP,
                         boton)
        pygame.draw.rect(sup, DORADO if hover else (230, 207, 177), boton, m.trazo())
        fuente_boton = fuente if boton.w >= p(154) else m.fuente(12)
        leyenda = fuente_boton.render(f"{tecla}  {etiqueta}", True, BLANCO if habilitado else GRIS)
        sup.blit(leyenda, leyenda.get_rect(center=boton.center))
        if habilitado:
            hotspots.append((boton, key))
    if lateral:
        y = ay + p(128)
        sup.blit(fuente.render("ÚLTIMOS SUCESOS", True, DORADO), (x, y))
        dibujar_mensajes(sup, fuente, x, y + p(28), foto,
                         max_lineas=max(1, (contenido.bottom - y - p(100)) // max(1, p(18))), ancho_max=w)
    if ayudas:
        chica = m.fuente(13)
        lineas = ("WASD / flechas: caminar · M: mapa",
                  "Tab: mochila · C: orden · U: rebobinar") if lateral else (
                      "WASD / flechas: caminar · Tab: mochila · M: mapa · U: rebobinar",)
        for i, linea in enumerate(lineas):
            sup.blit(chica.render(linea, True, GRIS),
                     (x, contenido.bottom - p(48) + i * p(18)))
    # En lateral el texto se ajusta a su columna.
    chica = m.fuente(13)
    pie = chica.render("F2 Controles · F10 Ajustes · Esc Pausa", True, DORADO)
    sup.blit(pie, (x, contenido.bottom - p(16)))
    # Accesos de ratón a la ayuda, ajustes y pausa, también disponibles sin ayudas.
    inicio = x
    for etiqueta, key in (("F2 Controles", pygame.K_F2),
                           ("F10 Ajustes", pygame.K_F10),
                           ("Esc Pausa", pygame.K_ESCAPE)):
        hotspots.append((pygame.Rect(inicio, contenido.bottom - p(16),
                                      chica.size(etiqueta)[0], p(18)), key))
        inicio += chica.size(etiqueta + " · ")[0]
    return hotspots


def dibujar_mensajes(sup: pygame.Surface, fuente: pygame.Font, x: int, y: int,
                     foto: "FotoEstado", max_lineas: int = 5,
                     ancho_max: int | None = None) -> None:
    """Panel con las últimas líneas de bitácora, humanizadas al jugador."""
    m = medidas(sup)
    p = m.px
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
            y += p(18)
            usadas += 1


def dibujar_toast(sup: pygame.Surface, fuente: pygame.Font, texto: str,
                  tope_inferior: int | None = None) -> None:
    """Error amable (guía §6): toast ajustado a 2 líneas; sigue.

    Con `tope_inferior` se apoya ahí (p. ej. sobre la banda de HUD) en
    lugar del borde de la ventana.
    """
    m = medidas(sup)
    p = m.px
    if not texto:
        return
    lineas = _texto.envolver(texto, fuente, sup.get_width() - p(36), 2)
    etiquetas = [fuente.render(parte, True, paleta.TEXTO_CLARO) for parte in lineas]
    alto = len(etiquetas) * p(22) + p(4)
    abajo = tope_inferior if tope_inferior is not None else sup.get_height() - p(10)
    fondo = pygame.Rect(p(10), abajo - alto,
                        max(e.get_width() for e in etiquetas) + p(16), alto)
    pygame.draw.rect(sup, ROJO, fondo)
    for i, etiqueta in enumerate(etiquetas):
        sup.blit(etiqueta, (fondo.x + p(8), fondo.y + p(2) + i * p(22)))
