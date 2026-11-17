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
DORADO = paleta.TEXTO_ACENTO
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
        lineas.append(f"* {_texto.inicial_mayuscula(nombre)}: {restante}")
    lineas.append(f"Pergaminos: {foto.pergaminos} (U)")
    if dev:
        lineas.append(f"[dev] solicitudes: {foto.presupuesto}")
    ancho = _ancho_panel(sup, x)
    for linea in lineas:
        for parte in _texto.envolver(linea, fuente, ancho, 99):
            sup.blit(fuente.render(parte, True, BLANCO), (x, y))
            y += fuente.get_linesize()
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
        sup.blit(fuente.render("(Vacía)", True, GRIS), (x, y))
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


def dibujar_contadores(sup, fuente, rect, foto, dev=False):
    """Datos en celdas estables; otra fila cuando el ancho no alcanza."""
    m=medidas(sup);f=m.estilo('datos');j=foto.jugador
    x,y=rect.x,rect.y;paso=f.get_linesize()
    campos=[(f"Vida {j.get('vida','?')}/{j.get('vida_max','?')}",160),
            (f"ATQ {j.get('ataque','?')}  DEF {j.get('defensa','?')}  VEL {j.get('velocidad','?')}",192),
            (f"Pergaminos {foto.pergaminos}",128)]
    campos += [(f'{n}: {v}',128) for n,v in (j.get('efectos',{}) or {}).items()]
    if dev: campos.append((f'[dev] solicitudes: {foto.presupuesto}',240))
    for cadena,ancho in campos:
        ancho=min(rect.width,m.ui_px(ancho))
        if x+ancho>rect.right and x>rect.x: x=rect.x;y+=paso
        _texto.etiqueta(sup,f,cadena,pygame.Rect(x,y,ancho,paso),BLANCO)
        x+=ancho+m.ui_px(8)
    return y+paso-rect.y


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
    p = m.ui_px
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


def alto_hud(sup):
    return medidas(sup).ui_px(248 if sup.get_width()<800 else 232)


def dibujar_hud(sup, fuente, rect, foto, sprites, sel_inv, orden, criterio, dev, ayudas, raton):
    """Jerarquía y tamaños de lectura independientes de la escala del escenario."""
    m=medidas(sup);p=m.ui_px
    fuente=m.estilo('cuerpo');chica=m.estilo('auxiliar');boton_f=m.estilo('boton')
    lateral=es_panoramica(sup)
    pygame.draw.rect(sup,paleta.PANEL,rect)
    pygame.draw.rect(sup,paleta.SECUNDARIO,rect,1)
    contenido=rect.inflate(-p(24),-p(24));x,y,w=contenido.x,contenido.y,contenido.w
    if lateral:
        cabecera=m.estilo('h3')
        sup.blit(cabecera.render('EXPLORADOR',True,DORADO),(x,y));y+=cabecera.get_linesize()
        dibujar_barra_vida(sup,x,y,w,foto);y+=p(24)
        y=dibujar_stats(sup,fuente,x,y,foto,dev)+p(8)
    else:
        y+=dibujar_contadores(sup,fuente,contenido,foto,dev)+p(8)
    inv=list(orden) if orden is not None else list(foto.inventario or [])
    inv_w=w if lateral else max(p(176),w//2-p(16))
    hotspots=dibujar_mochila(sup,fuente,pygame.Rect(x,y,inv_w,p(64)),foto,sprites,sel_inv,
        orden=orden,sufijo_orden=f' · {criterio}' if criterio else None)
    nombre=_texto.etiqueta_item(inv[sel_inv%len(inv)]) if inv else 'Tab o clic para seleccionar'
    etiqueta_y=y+p(24)+sprites.tam+p(16)
    _texto.etiqueta(sup,fuente,nombre,pygame.Rect(x,etiqueta_y,inv_w,fuente.get_linesize()*2),BLANCO,
        max_lineas=2,enfocado=bool(inv))
    ax=x if lateral else x+inv_w+p(16)
    ay=etiqueta_y+fuente.get_linesize()*2+p(8) if lateral else y
    aw=w if lateral else w-inv_w-p(16)
    acciones=(('E','Abrir',pygame.K_e,True),('Espacio','Atacar',pygame.K_SPACE,True),
              ('F','Recoger',pygame.K_f,True),('R','Usar',pygame.K_r,bool(inv)),
              ('Enter','Equipar',pygame.K_RETURN,bool(inv)),('Q','Soltar',pygame.K_q,bool(inv)))
    for i,(tecla,etiqueta,key,activo) in enumerate(acciones):
        ancho=(aw-p(8))//2
        boton=pygame.Rect(ax+(i%2)*(ancho+p(8)),ay+(i//2)*p(40),ancho,p(32))
        hover=activo and raton is not None and boton.collidepoint(raton)
        pygame.draw.rect(sup,(252,228,198) if hover else paleta.FONDO_APP,boton)
        pygame.draw.rect(sup,DORADO if hover else GRIS,boton,1)
        _texto.etiqueta(sup,boton_f,f'{tecla}  {etiqueta}',boton.inflate(-p(16),0),BLANCO if activo else GRIS,centrar=True)
        if activo: hotspots.append((boton,key))
    if lateral:
        y=ay+p(128)
        sup.blit(m.estilo('h3').render('ÚLTIMOS SUCESOS',True,DORADO),(x,y));y+=p(24)
        cantidad=max(0,(contenido.bottom-y-p(64))//fuente.get_linesize())
        dibujar_mensajes(sup,fuente,x,y,foto,max_lineas=cantidad,ancho_max=w)
    pie_y=contenido.bottom-p(40)
    if ayudas:
        ayuda='WASD / flechas: caminar · M: mapa · H: historial · U: rebobinar'
        _texto.etiqueta(sup,chica,ayuda,pygame.Rect(x,pie_y,w,chica.get_linesize()),GRIS)
    inicio=x;pie_y+=p(24)
    for etiqueta,key in (('F2 Controles',pygame.K_F2),('F10 Ajustes',pygame.K_F10),('Esc Pausa',pygame.K_ESCAPE)):
        ancho=chica.size(etiqueta)[0]
        sup.blit(chica.render(etiqueta,True,DORADO),(inicio,pie_y))
        hotspots.append((pygame.Rect(inicio,pie_y,ancho,chica.get_linesize()),key))
        inicio+=ancho+p(16)
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
        for parte in _texto.envolver(_texto.inicial_mayuscula(_texto.humanizar(linea)), fuente, ancho,
                                     max_lineas - usadas):
            if usadas >= max_lineas:
                return
            sup.blit(fuente.render(parte, True, GRIS), (x, y))
            y += fuente.get_linesize()
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
    lineas = _texto.envolver(_texto.inicial_mayuscula(texto), fuente, sup.get_width() - p(36), 2)
    etiquetas = [fuente.render(parte, True, paleta.TEXTO_CLARO) for parte in lineas]
    alto = len(etiquetas) * p(22) + p(4)
    abajo = tope_inferior if tope_inferior is not None else sup.get_height() - p(10)
    fondo = pygame.Rect(p(10), abajo - alto,
                        max(e.get_width() for e in etiquetas) + p(16), alto)
    pygame.draw.rect(sup, ROJO, fondo)
    for i, etiqueta in enumerate(etiquetas):
        sup.blit(etiqueta, (fondo.x + p(8), fondo.y + p(2) + i * p(22)))
