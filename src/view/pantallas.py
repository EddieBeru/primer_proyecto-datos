"""Pantallas 1.1-1.7 (Parte 1 §1 + guía §9): menú, selección, carga, juego,
fin, error amable y versión incompatible. Cada una dibuja desde datos que le
pasa el App (nunca tocan Sesión directamente, salvo juego vía callbacks).

Menús (rework 18/10/2026): jerarquía gráfica en vez de listas de texto —
logo con arte, botones con número, tarjetas de cripta con pictogramas
(salas + puntos de dificultad) y pantalla final con arte y resumen. Un solo
tipo de letra (monoespaciada del juego) en varios tamaños; los datos de la
bitácora se humanizan con `texto.humanizar`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.view import capas
from src.view import paleta
from src.view import texto as _texto
from src.view import ui
from src.view.display import RESOLUCIONES
from src.view.medidas import medidas
from src.view.sprites import (CAJA_ARTE_ALTO, CAJA_ARTE_ANCHO,
                              LID_STAGES, SpriteManager)

if TYPE_CHECKING:  # solo tipos: en runtime la vista solo importa Sesion
    from src.controller2.fachada import FotoEstado

BLANCO = paleta.TEXTO
GRIS = paleta.SECUNDARIO
DORADO = paleta.TEXTO_ACENTO
FONDO = paleta.FONDO_APP

DAMERO_FONDO = (250, 233, 209)  # damero sutil del fondo de menús

# Tamaños fijos (registro producto: escala consistente, no fluida).
T_DISPLAY, T_TITULO, T_BOTON, T_CUERPO, T_NOTA = 64, 28, 14, 16, 12
CONTROLES = ("WASD/flechas mover · E abrir · Espacio atacar · X objetivo · "
             "F recoger · Tab mochila (Shift atrás) · C orden · Enter equipar · "
             "R usar · Esc pausa")


def _fuente(tam: int, negrita: bool = False):
    from src.view.tipografia import fuente
    return fuente(tam, negrita)


class _DisposicionPanel:
    """Distribuye medidas de UI; texto y arte se dibujan a resolución nativa."""

    def __init__(self, sup: pygame.Surface):
        self.sup = sup
        self.factor = medidas(sup).factor
        self.x = (sup.get_width() - round(920 * self.factor)) // 2
        self.y = (sup.get_height() - round(720 * self.factor)) // 2

    def rect(self, x, y, w, h):
        return pygame.Rect(self.x + round(x * self.factor),
                           self.y + round(y * self.factor),
                           round(w * self.factor), round(h * self.factor))

    def fuente(self, tam, negrita=False):
        return medidas(self.sup).fuente(tam, negrita)


def _texto_sombra(sup: pygame.Surface, fuente: pygame.Font, texto: str,
                  centro: tuple[int, int], color, sombra=(90, 45, 10)) -> None:
    """Texto con sombra dura: lo hace legible sobre el damero y da peso."""
    m = medidas(sup)
    p = m.px
    etiqueta = fuente.render(texto, True, color)
    x = centro[0] - etiqueta.get_width() // 2
    y = centro[1] - etiqueta.get_height() // 2
    if sombra is not None:
        negativo = fuente.render(texto, True, sombra)
        sup.blit(negativo, (x + p(2), y + p(2)))
    sup.blit(etiqueta, (x, y))


def _fondo_menu(sup: pygame.Surface) -> None:
    """Fondo común: crema + damero sutil, como el piso de la sala."""
    m = medidas(sup)
    p = m.px
    sup.fill(FONDO)
    lado = max(1,p(40))
    for fy in range(0, sup.get_height() // lado):
        for fx in range(0, sup.get_width() // lado):
            if (fx + fy) % 2:
                sup.fill(DAMERO_FONDO,
                         pygame.Rect(fx * lado, fy * lado, lado, lado))


def _panel(sup: pygame.Surface, rect: pygame.Rect,
           fondo=paleta.PANEL, borde=DORADO) -> None:
    """Panel/ tarjeta estándar: rectángulo duro (estética pixel, sin radios)."""
    m = medidas(sup)
    p = m.px
    pygame.draw.rect(sup, fondo, rect)
    pygame.draw.rect(sup, borde, rect, m.trazo(3))


def _insignia(sup: pygame.Surface, centro: tuple[int, int], numero: str,
              color=DORADO, texto_claro=True, lado: int = 36) -> None:
    """Cuadrado con la tecla (la interacción se ve de un vistazo).

    Teclas de más de un carácter ("Esc") usan letra más chica para que no
    se salgan del recuadro. Todo a escuadra: nada de círculos.
    """
    m = medidas(sup)
    p = m.px
    rect = pygame.Rect(0, 0, lado, lado)
    rect.center = centro
    pygame.draw.rect(sup, color, rect)
    pygame.draw.rect(sup, (255, 255, 255), rect, m.trazo(2))
    fuente = _fuente(min(p(T_NOTA), lado // 2), negrita=True) if len(numero) > 1 else _fuente(
        min(p(T_CUERPO), lado - p(8)), negrita=True)
    etiqueta = fuente.render(numero, True,
                             paleta.TEXTO_CLARO if texto_claro else BLANCO)
    sup.blit(etiqueta, (centro[0] - etiqueta.get_width() // 2,
                        centro[1] - etiqueta.get_height() // 2))


def boton(sup: pygame.Surface, rect: pygame.Rect, tecla: str, etiqueta: str,
          nota: str = "", primario: bool = False, habilitado: bool = True,
          resaltado: bool = False) -> pygame.Rect:
    """Botón de menú: insignia de tecla + etiqueta + nota secundaria.

    `primario` (acción principal) va en naranja lleno; el resto en panel
    claro con borde. Deshabilitado: gris y nota visible (no se oculta).
    `resaltado` (ratón encima) aclara el panel; retorna su rect.
    """
    m = medidas(sup)
    p = m.px
    if habilitado and primario:
        fondo, borde, color = DORADO, (150, 60, 0), paleta.TEXTO_CLARO
        if resaltado:
            fondo = (130, 48, 0)
    elif habilitado:
        fondo, borde, color = paleta.PANEL, DORADO, BLANCO
        if resaltado:
            fondo, borde = (252, 228, 198), (160, 70, 0)
    else:
        fondo, borde, color = (238, 228, 214), (185, 170, 150), paleta.SECUNDARIO
    _panel(sup, rect, fondo, borde)
    _insignia(sup,(rect.x+m.ui_px(24),rect.centery),tecla,
              color=paleta.ACCION,texto_claro=True,lado=min(m.ui_px(32),rect.h-8))
    fuente = m.estilo('boton')
    x = rect.x + m.ui_px(48)
    alto = fuente.get_height()
    y = rect.centery - alto // 2 - (m.estilo('auxiliar').get_linesize()//2 if nota else 0)
    _texto.etiqueta(sup, fuente, etiqueta,
                    pygame.Rect(x,y,max(1,rect.right-x-p(8)),alto), color)
    if nota:
        color_nota = paleta.TEXTO_CLARO if (habilitado and primario) else (color if not habilitado else GRIS)
        fuente_nota = m.estilo('auxiliar')
        _texto.etiqueta(sup,fuente_nota,nota,
                        pygame.Rect(x,y+fuente.get_linesize(),max(1,rect.right-x-p(8)),fuente_nota.get_height()),color_nota)
    return rect


def _prota(sup: pygame.Surface, sprites: SpriteManager | None,
           centro: tuple[int, int], escala: float = 2.0,
           espejo: bool = False, tinte=None) -> None:
    """El prota en grande para los menús.

    Usa el PNG nativo (`jugador_grande`, nearest): en partida el sprite
    se reduce a TAM para el look retro, pero en menús esa reducción se veía
    pixelada al agrandarla. `escala` = factor sobre el arte nativo 117×161.
    """
    m = medidas(sup)
    p = m.px
    if sprites is None:
        return
    try:
        img = sprites.jugador_grande(escala * m.factor, espejo)
    except Exception:
        img, _ = sprites.jugador_frame(False, 0, "S", 0, espejo=espejo)
        img = pygame.transform.scale(
            img, (round(img.get_width() * escala * 3),
                  round(img.get_height() * escala * 3)))
    if tinte is not None:
        img = img.copy()
        img.fill(tinte, special_flags=pygame.BLEND_MULT)
    sup.blit(img, (centro[0] - img.get_width() // 2,
                   centro[1] - img.get_height() // 2))


def _adorno(sup: pygame.Surface, sprites: SpriteManager | None,
            metodo: str, centro: tuple[int, int], escala: int = 2) -> None:
    """Pieza de sprite (escudo, espada, llave…) escalada como adorno."""
    if sprites is None:
        return
    try:
        img = getattr(sprites, metodo)()
    except Exception:
        return
    img = pygame.transform.scale(
        img, (img.get_width() * escala, img.get_height() * escala))
    sup.blit(img, (centro[0] - img.get_width() // 2,
                   centro[1] - img.get_height() // 2))


def _puntos_dificultad(sup: pygame.Surface, x: int, y: int, nivel: int,
                       maximo: int = 5) -> int:
    """Dificultad como pepperoni a escuadra (leer de un vistazo)."""
    m = medidas(sup)
    p = m.px
    try:
        nivel = max(0, min(int(nivel), maximo))
    except (TypeError, ValueError):
        nivel = 0
    lado, hueco = max(4,p(14)), max(4,p(6))
    for i in range(maximo):
        rect = pygame.Rect(x + i * (lado + hueco), y - lado // 2, lado, lado)
        if i < nivel:
            pygame.draw.rect(sup, paleta.PELIGRO, rect)
            pygame.draw.rect(sup, (140, 20, 10), rect, 2)
        else:
            pygame.draw.rect(sup, (225, 205, 180), rect)
            pygame.draw.rect(sup, (200, 178, 152), rect, 2)
    return x + maximo * (lado + hueco)


def _titulo(sup: pygame.Surface, fuente: pygame.Font, texto: str, y: int = 60) -> int:
    m = medidas(sup)
    p = m.px
    _texto_sombra(sup, m.fuente(T_TITULO, negrita=True), texto,
                  (sup.get_width() // 2, y + p(16)), DORADO)
    return y + p(50)


def _encima(rect: pygame.Rect, raton: tuple[int, int] | None) -> bool:
    """True si el ratón está sobre el rect (ratón puede no haberse movido)."""
    return raton is not None and rect.collidepoint(raton)


def _pie(sup: pygame.Surface, texto: str, color=None) -> None:
    """Línea de ayuda al pie, siempre igual en todos los menús."""
    m = medidas(sup)
    p = m.px
    etiqueta = m.fuente(T_NOTA).render(_texto.inicial_mayuscula(texto), True, color or GRIS)
    sup.blit(etiqueta, (sup.get_width() // 2 - etiqueta.get_width() // 2,
                        sup.get_height() - p(34)))


def stage_caja(apertura: int | None) -> int:
    """Fotograma de la tapa (1-6) del menú según frames desde entrar.

    None = menú ya abierto (frame final, el de las pruebas). Con número:
    ~30 frames de caja cerrada y 10 por cada stage de apertura (2-5).
    """
    if apertura is None or apertura >= 70:
        return LID_STAGES
    if apertura < 30:
        return 1
    return 2 + (apertura - 30) // 10


CAJA_MENU_ALTO = 380  # alto de la caja en los menús (arriba, centrada)


def rect_caja_menu(sup: pygame.Surface) -> pygame.Rect:
    """Rect de la caja del menú (arriba, centrada); origen del zoom."""
    m = medidas(sup)
    p = m.px
    alto = min(p(CAJA_MENU_ALTO), round(sup.get_height() * 0.46))
    rect = pygame.Rect(0, 0, round(alto * CAJA_ARTE_ANCHO / CAJA_ARTE_ALTO), alto)
    rect.midtop = (sup.get_width() // 2, p(14))
    return rect


def _caja_menu(sup: pygame.Surface, sprites: SpriteManager | None,
               titulo: str | None = None, color: tuple = DORADO,
               sub: str | None = None,
               stage: int = LID_STAGES) -> pygame.Rect:
    """Caja arriba con el título adentro; retorna su rect.

    Mismo layout en todos los menús (caja arriba, opciones abajo) y mismo
    rect que usa el zoom menú -> partida.
    """
    m = medidas(sup)
    p = m.px
    rect = rect_caja_menu(sup)
    if sprites is not None:
        capas.dibujar_caja_cuerpo(sup, sprites, rect)
    if titulo:
        fuente_t = m.fuente(T_BOTON, negrita=True)
        for tam in ((max(24,p(T_DISPLAY)),) if titulo=="CRIPTA" else (28,24)):
            candidata = m.fuente(tam, negrita=True)
            if candidata.size(titulo)[0] <= rect.w - p(44):
                fuente_t = candidata
                break
        imagen = fuente_t.render(titulo, True, paleta.TEXTO)
        respaldo = imagen.get_rect(center=rect.center).inflate(16, 8)
        pygame.draw.rect(sup, paleta.PANEL, respaldo)
        sup.blit(imagen, imagen.get_rect(center=rect.center))
    if sub:
        fuente_sub = m.estilo('auxiliar')
        lineas = _texto.envolver(sub, fuente_sub, rect.w - 16, 3)
        respaldo = pygame.Rect(0, 0, rect.w - 8, len(lineas)*fuente_sub.get_linesize()+8)
        respaldo.midtop = (rect.centerx, rect.centery + fuente_t.get_height()//2 + 8)
        pygame.draw.rect(sup, paleta.PANEL, respaldo)
        _texto.etiqueta(sup, fuente_sub, sub, respaldo.inflate(-8,-8), GRIS, max_lineas=3)
    if sprites is not None:
        capas.dibujar_caja_tapa(sup, sprites, rect, stage)
    return rect


def pantalla_inicio(sup: pygame.Surface, fuente: pygame.Font,
                    puede_continuar: bool,
                    sprites: SpriteManager | None = None,
                    apertura: int | None = None,
                    raton: tuple[int, int] | None = None
                    ) -> list[tuple[pygame.Rect, int]]:
    """1.1 Menú: la caja de pizza se abre (stages 1-6) y el título va dentro.

    Los lid dibujan la tapa girando; el título se pinta entre el cuerpo y
    la tapa, así la tapa cerrada lo esconde y la apertura lo revela.
    """
    m = medidas(sup)
    p = m.px
    _fondo_menu(sup)
    _caja_menu(sup, sprites, "CRIPTA", sub="Explora · saquea · sobrevive",
               stage=stage_caja(apertura))

    # El prota asoma por la derecha, ya sin fondo ni cajas.
    _prota(sup, sprites, (sup.get_width() - p(95), 190), 1.2)

    ancho_b, hueco_b = min(p(250), (sup.get_width() - p(64)) // 3), p(16)
    y = min(p(530), sup.get_height() - p(190))
    x0 = sup.get_width() // 2 - (3 * ancho_b + 2 * hueco_b) // 2
    rects = [
        pygame.Rect(x0, y, ancho_b, p(74)),
        pygame.Rect(x0 + ancho_b + hueco_b, y, ancho_b, p(74)),
        pygame.Rect(x0 + 2 * (ancho_b + hueco_b), y, ancho_b, p(74)),
    ]
    boton(sup, rects[0], "1", "Jugar", "Elige tu cripta", primario=True,
          resaltado=_encima(rects[0], raton))
    boton(sup, rects[1], "2", "Continuar",
          "Partida guardada" if puede_continuar else "Sin guardado aún",
          habilitado=puede_continuar, resaltado=_encima(rects[1], raton))
    boton(sup, rects[2], "3", "Salir", "", resaltado=_encima(rects[2], raton))
    _pie(sup, "Pulsa el número o haz clic en la opción")
    hotspots = [(rects[0], pygame.K_1)]
    if puede_continuar:
        hotspots.append((rects[1], pygame.K_2))
    hotspots.append((rects[2], pygame.K_3))
    for i, (tecla, etiqueta, key) in enumerate((("F10", "Ajustes", pygame.K_F10),
                                              ("F2", "Controles", pygame.K_F2))):
        rect = pygame.Rect(sup.get_width() // 2 - p(250) + i * p(260), y + p(90), p(240), p(56))
        boton(sup, rect, tecla, etiqueta, resaltado=_encima(rect, raton))
        hotspots.append((rect, key))
    return hotspots


def _tarjeta_cripta(sup: pygame.Surface, rect: pygame.Rect, numero: int,
                    nombre: str, salas, dificultad,
                    resaltada: bool = False) -> None:
    """Tarjeta compacta de cripta: número, nombre, salas y picante."""
    m = medidas(sup)
    p = m.px
    _panel(sup, rect, (252, 228, 198) if resaltada else paleta.PANEL,
           (160, 70, 0) if resaltada else DORADO)
    _insignia(sup, (rect.x + p(30), rect.centery), str(numero))
    fuente_nombre = m.fuente(T_CUERPO, negrita=True)
    nombre_rect = pygame.Rect(rect.x+p(58),rect.y+8,rect.w-p(70),fuente_nombre.get_linesize())
    _texto.etiqueta(sup,fuente_nombre,nombre,nombre_rect,BLANCO)
    # Salas: puerta a escuadra + número.
    pygame.draw.rect(sup, paleta.MURO,
                     pygame.Rect(rect.x + p(58), rect.bottom - p(28), 14, 18))
    pygame.draw.rect(sup, paleta.PUERTA_ABIERTA,
                     pygame.Rect(rect.x + p(61), rect.bottom - p(25), 8, 12))
    sup.blit(m.fuente(T_NOTA).render(f"Salas: {salas}", True, GRIS),
             (rect.x + p(78), rect.bottom - p(27)))
    _puntos_dificultad(sup, rect.right - p(104), rect.bottom - p(19), dificultad)


def pantalla_seleccion(sup: pygame.Surface, fuente: pygame.Font,
                       criptas: list,
                       sprites: SpriteManager | None = None,
                       raton: tuple[int, int] | None = None
                       ) -> list[tuple[pygame.Rect, int]]:
    """1.2 Tarjetas de cripta bajo la caja: elegir de un vistazo."""
    m = medidas(sup)
    p = m.px
    _fondo_menu(sup)
    rect_caja = _caja_menu(sup, sprites, "Elige tu cripta",
                           sub="Pulsa el número de la cripta · Esc vuelve")
    total = max(len(criptas), 1)
    columnas = 2 if total <= 4 else 3
    hueco = p(12)
    ancho = (sup.get_width() - p(40) - hueco * (columnas - 1)) // columnas
    filas = (total + columnas - 1) // columnas
    y0 = rect_caja.bottom + p(18)
    disponible = sup.get_height() - p(40) - y0
    alto = max(p(54), min(p(92), (disponible - hueco * (filas - 1)) // filas))
    x0 = sup.get_width() // 2 - (columnas * ancho + hueco * (columnas - 1)) // 2
    hotspots: list[tuple[pygame.Rect, int]] = []
    for i, cripta in enumerate(criptas):
        fila, col = divmod(i, columnas)
        rect = pygame.Rect(x0 + col * (ancho + hueco),
                           y0 + fila * (alto + hueco), ancho, alto)
        nombre = str(cripta.get("nombre", cripta.get("id", "?")))
        _tarjeta_cripta(sup, rect, i + 1, nombre,
                        cripta.get("salas", "?"), cripta.get("dificultad", 0),
                        resaltada=_encima(rect, raton))
        if i < 9:
            hotspots.append((rect, pygame.K_1 + i))
    _pie(sup, "1-9 o clic elige · Esc vuelve al menú")
    return hotspots


def pantalla_carga(sup: pygame.Surface, fuente: pygame.Font,
                   detalle: str = "Preparando la cripta…",
                   sprites: SpriteManager | None = None) -> None:
    """1.3 Carga + aviso 429 («esperando N s…», guía §5: sin congelar)."""
    m = medidas(sup)
    p = m.px
    _fondo_menu(sup)
    rect_caja = _caja_menu(sup, sprites)
    cx, cy = sup.get_width() // 2, rect_caja.bottom + 96
    # Pizza a escuadra: caja, masa, queso y pepperoni (todo rectángulos).
    caja = pygame.Rect(0, 0, 56, 56)
    caja.center = (cx, cy)
    pygame.draw.rect(sup, paleta.MURO, caja)
    pygame.draw.rect(sup, FONDO, caja.inflate(-8, -8))
    pygame.draw.rect(sup, (255, 196, 92), caja.inflate(-14, -14))
    for dx, dy in ((-12, -12), (12, -12), (-12, 12), (12, 12), (0, 0)):
        pep = pygame.Rect(0, 0, 8, 8)
        pep.center = (cx + dx, cy + dy)
        pygame.draw.rect(sup, paleta.PELIGRO, pep)
    etiqueta = m.fuente(T_BOTON, negrita=True).render(_texto.inicial_mayuscula(detalle), True, BLANCO)
    sup.blit(etiqueta, (sup.get_width() // 2 - etiqueta.get_width() // 2,
                        cy + p(48)))


def pantalla_juego(sup: pygame.Surface, fuente: pygame.Font, foto: "FotoEstado",
                   sprites: SpriteManager, area_sala: pygame.Rect,
                   sel_enemigo: int = 0, sel_suelo: int = 0, sel_inv: int = 0,
                   ref_vida: dict | None = None, dev: bool = False,
                   facing: str = "N", desplaza: tuple[int, int] = (0, 0),
                   paso_jugador: tuple[bool, int, int] = (False, 0, 0),
                   pos_jugador: tuple[float, float] | None = None,
                   golpe: str | None = None,
                   alcance: frozenset = frozenset(),
                   spots: tuple[list, list] | None = None,
                   tinte_dano: bool = False,
                   tajo: tuple[str, float] | None = None,
                   espejo: bool | None = None,
                   trampas_fuego: dict[str, float] | None = None,
                   golpes: dict[str, float] | None = None,
                   mostrar_canvas: bool = True,
                   orden_inv: list | None = None,
                   criterio_inv: str | None = None,
                   mostrar_ayudas: bool = True,
                   raton: tuple[int, int] | None = None) -> list:
    """1.4 Sala + actores + HUD. Toda la lectura sale de la foto.

    `orden_inv`/`criterio_inv`: copia ordenada de la mochila ya calculada
    por la Sesión (§4.5); la vista solo la dibuja, nunca ordena.

    Distribución: canvas arriba centrado (4 partes) y banda de información
    abajo (1 parte): contadores en una línea y mochila horizontal debajo.
    """
    m = medidas(sup)
    p = m.px
    sup.fill(FONDO)
    titulo = fuente.render(f"Sala {foto.sala_id}: {_texto.inicial_mayuscula(foto.sala_nombre)} [{_texto.inicial_mayuscula(foto.estado)}]",
                           True, DORADO)
    sup.blit(titulo, titulo.get_rect(midtop=(area_sala.centerx, p(8))))
    pygame.draw.line(sup, DORADO, (p(10), p(30)),
                     (sup.get_width() - p(10), p(30)), m.trazo(2))
    if mostrar_canvas:
        # El zoom menú -> caja esconde el canvas: solo se ve la caja encogiendo.
        capas.dibujar_fondo(sup, area_sala, foto, sprites, fuente)
        capas.dibujar_estatica(sup, area_sala, foto, sprites, sel_suelo, fuente,
                               spots, trampas_fuego)
        capas.dibujar_actores(sup, area_sala, foto, sprites, fuente,
                              sel_enemigo, ref_vida, facing, desplaza,
                              paso_jugador, pos_jugador, golpe, alcance,
                              tinte_dano, tajo, espejo, golpes)
        # Mejoras 2026-10: sala oscura -> velo con halo (o luz con antorcha).
        capas.dibujar_oscuridad(sup, area_sala, foto, pos_jugador)
    linea = capas.rect_caja(area_sala).bottom + p(2)
    if ui.es_panoramica(sup):
        zona = pygame.Rect(sup.get_width() - m.ui_px(ui.ANCHO_LATERAL) - p(16), p(46),
                           m.ui_px(ui.ANCHO_LATERAL), sup.get_height() - p(62))
    else:
        zona = pygame.Rect(p(14), linea + p(4), sup.get_width() - p(28),
                           sup.get_height() - linea - p(14))
    hotspots = ui.dibujar_hud(sup, fuente, zona, foto, sprites, sel_inv,
                              orden_inv, criterio_inv, dev, mostrar_ayudas, raton)
    ui.dibujar_toast(sup, fuente, foto.error or "", tope_inferior=linea - p(4))
    return hotspots


def _resumen_final(sup: pygame.Surface, rect: pygame.Rect, foto: "FotoEstado",
                   reporte: dict | None) -> int:
    """Filas etiqueta -> valor del resumen final. Retorna la y final.

    Si el valor no cabe a la derecha de la etiqueta, baja a su propia
    línea (nombres de sala largos, rutas…): nunca se solapan.
    """
    m = medidas(sup)
    p = m.px
    filas = [
        ("Sala alcanzada", f"{foto.sala_id} — {foto.sala_nombre}"),
        ("Pergaminos", str(foto.pergaminos)),
        ("Puntos de vida", str(foto.jugador.get("vida", "?"))),
    ]
    if reporte and reporte.get("terminada") and reporte.get("red"):
        red = reporte["red"]
        filas.insert(2, ("Peticiones a la cripta",
                         f"{red.get('realizadas', '?')} de {red.get('presupuesto', '?')}"))

    fuente_et = m.fuente(T_CUERPO)
    fuente_val = m.fuente(T_CUERPO, negrita=True)
    y = rect.y + p(14)
    x_izq, x_der = rect.x + p(20), rect.right - p(20)
    for etiqueta, valor in filas:
        izq = fuente_et.render(etiqueta, True, GRIS)
        der = fuente_val.render(str(valor), True, BLANCO)
        cabe = x_izq + izq.get_width() + p(16) + der.get_width() <= x_der
        sup.blit(izq, (x_izq, y))
        if cabe:
            sup.blit(der, (x_der - der.get_width(), y))
            y += fuente_et.get_linesize()+4
        else:
            y += fuente_et.get_linesize()
            valor_rect = pygame.Rect(x_izq+p(10),y,x_der-x_izq-p(10),fuente_val.get_linesize())
            _texto.etiqueta(sup,fuente_val,str(valor),valor_rect,BLANCO)
            y += fuente_val.get_linesize()+4
        pygame.draw.line(sup, (232, 214, 190),
                         (x_izq, y - p(6)), (x_der, y - p(6)))
    return y


def pantalla_fin(sup: pygame.Surface, fuente: pygame.Font, foto: "FotoEstado",
                 reporte: dict | None = None,
                 sprites: SpriteManager | None = None,
                 raton: tuple[int, int] | None = None
                 ) -> list[tuple[pygame.Rect, int]]:
    """1.5 Victoria / derrota: caja arriba, resumen y acciones abajo (guía §9)."""
    m = medidas(sup)
    p = m.px
    _fondo_menu(sup)
    gano = foto.estado == "victoria"
    color = paleta.VIDA if gano else paleta.PELIGRO
    rect_caja = _caja_menu(sup, sprites, "¡VICTORIA!" if gano else "DERROTA",
                           color=color,
                           sub="Escapaste con el botín" if gano
                           else "La cripta te venció… esta vez")

    y_fila = rect_caja.bottom + p(26)
    # El prota (rojo si cayó), con el botín al ganar.
    _prota(sup, sprites, (p(150), y_fila + p(100)), 1.2,
           tinte=None if gano else (255, 120, 120))
    if gano:
        _adorno(sup, sprites, "escudo", (p(64), y_fila + p(60)), 2)
        _adorno(sup, sprites, "espada", (p(238), y_fila + p(56)), 2)

    # Resumen con datos legibles (nada de diccionarios crudos).
    rect = pygame.Rect(sup.get_width() - p(40) - p(372), y_fila, p(372), p(210))
    if sup.get_width()<800:
        rect = pygame.Rect(200,y_fila,sup.get_width()-224,p(210))
    _panel(sup, rect)
    _resumen_final(sup, rect, foto, reporte)

    # Últimos sucesos humanizados + pie técnico en la columna central.
    x_col, ancho_col = p(300), p(250)
    y = y_fila + p(8)
    for linea in [_texto.humanizar(m) for m in (foto.mensajes or [])[-3:]]:
        for parte in _texto.envolver(linea, fuente, ancho_col, 1):
            sup.blit(fuente.render(parte, True, GRIS), (x_col, y))
            y += p(18)
    if reporte and reporte.get("puntajes_ruta"):
        for parte in _texto.envolver(f"Puntajes: {reporte['puntajes_ruta']}",
                                     fuente, ancho_col, 1):
            sup.blit(fuente.render(parte, True, paleta.SECUNDARIO), (x_col, y))
            y += p(18)
    if reporte and reporte.get("puntaje_error"):
        error = f"No se guardó el puntaje: {reporte['puntaje_error']}"
        for parte in _texto.envolver(error, fuente, ancho_col, 2):
            sup.blit(fuente.render(parte, True, paleta.PELIGRO), (x_col, y))
            y += p(18)

    ancho_b, hueco_b = min(p(410), (sup.get_width() - p(60)) // 2), p(20)
    x0 = sup.get_width() // 2 - (2 * ancho_b + hueco_b) // 2
    y_b = sup.get_height() - p(100)
    b1 = pygame.Rect(x0, y_b, ancho_b, p(60))
    b2 = pygame.Rect(x0 + ancho_b + hueco_b, y_b, ancho_b, p(60))
    boton(sup, b1, "1", "Jugar de nuevo", "Otra partida de la misma cripta" if b1.h>=48 else "",
          primario=True, resaltado=_encima(b1, raton))
    boton(sup, b2, "2", "Volver al menú", "", resaltado=_encima(b2, raton))
    return [(b1, pygame.K_1), (b2, pygame.K_2)]


def pantalla_error(sup: pygame.Surface, fuente: pygame.Font, mensaje: str,
                   sprites: SpriteManager | None = None,
                   raton: tuple[int, int] | None = None
                   ) -> list[tuple[pygame.Rect, int]]:
    """1.6 Error amable a pantalla completa (red, presupuesto, guardado)."""
    m = medidas(sup)
    p = m.px
    sup.fill(paleta.PELIGRO_FONDO)
    rect_caja = _caja_menu(sup, sprites, "Algo salió mal",
                           color=paleta.TEXTO_CLARO,
                           sub="Tu partida sigue a salvo")
    fuente_cuerpo = m.fuente(T_CUERPO)
    y = rect_caja.bottom + p(26)
    ancho = sup.get_width() - 48
    lineas = _texto.envolver(mensaje, fuente_cuerpo, ancho, 4)
    alto = len(lineas) * fuente_cuerpo.get_linesize()
    _texto.etiqueta(sup, fuente_cuerpo, mensaje, pygame.Rect(24,y,ancho,alto),
                    paleta.TEXTO_CLARO, max_lineas=4, enfocado=True)
    y += alto
    boton_volver = pygame.Rect(0, 0, p(340), p(56))
    boton_volver.midtop = (sup.get_width() // 2, y + p(10))
    boton(sup, boton_volver, "Esc", "Volver al menú", "",
          resaltado=_encima(boton_volver, raton))
    _pie(sup, "Esc o el botón vuelven al menú", paleta.TEXTO_CLARO)
    return [(boton_volver, pygame.K_ESCAPE)]


def pantalla_version(sup: pygame.Surface, fuente: pygame.Font, mensaje: str,
                     sprites: SpriteManager | None = None,
                     raton: tuple[int, int] | None = None
                     ) -> list[tuple[pygame.Rect, int]]:
    """1.7 Partida de versión anterior: nunca cargar a medias (guía §9)."""
    m = medidas(sup)
    p = m.px
    _fondo_menu(sup)
    rect_caja = _caja_menu(sup, sprites, "Versión anterior",
                           sub="Tu guardado no se cargó a medias")
    fuente_cuerpo = m.fuente(T_CUERPO)
    y = rect_caja.bottom + p(26)
    ancho = sup.get_width() - 48
    lineas = _texto.envolver(mensaje, fuente_cuerpo, ancho, 4)
    alto = len(lineas) * fuente_cuerpo.get_linesize()
    _texto.etiqueta(sup, fuente_cuerpo, mensaje, pygame.Rect(24,y,ancho,alto),
                    BLANCO, max_lineas=4, enfocado=True)
    y += alto
    boton_volver = pygame.Rect(0, 0, p(340), p(56))
    boton_volver.midtop = (sup.get_width() // 2, y + p(10))
    boton(sup, boton_volver, "Esc", "Volver al menú", "",
          resaltado=_encima(boton_volver, raton))
    _pie(sup, "Esc o el botón vuelven al menú")
    return [(boton_volver, pygame.K_ESCAPE)]


def menu_pausa(sup: pygame.Surface, fuente: pygame.Font,
               sprites: SpriteManager | None = None,
               raton: tuple[int, int] | None = None
               ) -> list[tuple[pygame.Rect, int]]:
    """Pausa (Esc): menú local; guardar/cargar/salir vía Sesión en el App."""
    m = medidas(sup)
    p = m.px
    _fondo_menu(sup)
    _titulo(sup, m.fuente(T_TITULO, True), "Pausa", y=min(p(64), sup.get_height() // 12))
    alto, separacion = m.ui_px(48), m.ui_px(8)
    y = min(p(270), sup.get_height()-6*(alto+separacion)-m.ui_px(24))
    if sup.get_height() >= m.ui_px(800):
        _prota(sup, sprites, (sup.get_width() // 2, y - p(90)), 1.0)
    ancho = min(m.ui_px(460),sup.get_width()-m.ui_px(48))
    x = sup.get_width() // 2 - ancho // 2
    hotspots: list[tuple[pygame.Rect, int]] = []
    for tecla, etiqueta, nota, codigo in (
            ("G", "Guardar", "Guarda la partida actual", pygame.K_g),
            ("C", "Cargar", "Retoma el último guardado", pygame.K_c),
            ("F10", "Ajustes", "Ventana y pantalla completa", pygame.K_F10),
            ("F2", "Controles", "Guía de teclado y ratón", pygame.K_F2),
            ("Esc", "Volver", "Sigue jugando", pygame.K_ESCAPE),
            ("Q", "Salir al menú", "No pierde el guardado", pygame.K_q)):
        rect = pygame.Rect(x, y, ancho, alto)
        boton(sup, rect, tecla, etiqueta, nota,
              resaltado=_encima(rect, raton))
        hotspots.append((rect, codigo))
        y += alto + separacion
    return hotspots


def pantalla_ajustes(sup, fuente, tamano, completa, ayudas, raton=None):
    _fondo_menu(sup)
    m=medidas(sup);p=m.ui_px;compacta=sup.get_height()<p(640)
    margen=24;ancho=sup.get_width()-margen*2
    titulo=m.estilo('h1');label=m.estilo('label');nota_f=m.estilo('auxiliar')
    sup.blit(titulo.render('Ajustes',True,DORADO),(margen,16))
    nota='Arrastra un borde para ajustar la ventana. F11: pantalla completa.'
    _texto.etiqueta(sup,nota_f,nota,pygame.Rect(margen,56,ancho,nota_f.get_linesize()),GRIS)
    sup.blit(m.estilo('h3').render('TAMAÑO DE VENTANA',True,DORADO),(margen,88))
    y=120;alto=p(48 if compacta else 64);gap=p(8);columna=(ancho-gap)//2
    hotspots=[]
    for i,(w,h) in enumerate(RESOLUCIONES):
        rect=pygame.Rect(margen+(i%2)*(columna+gap),y+(i//2)*(alto+gap),columna,alto)
        activo=not completa and tamano==(w,h)
        boton(sup,rect,str(i+1),f'{w} × {h}',('Clásica' if i==0 else 'Panorámica 16:9')+(' · activa' if activo else ''),
              primario=activo,resaltado=_encima(rect,raton))
        hotspots.append((rect,pygame.K_1+i))
    y+=2*(alto+gap)
    _texto.etiqueta(sup,label,f"{'Pantalla completa' if completa else 'Ventana'} · {sup.get_width()} × {sup.get_height()}",
                    pygame.Rect(margen,y,ancho,label.get_linesize()),GRIS)
    y+=label.get_linesize()+gap
    opciones=(('F11','Pantalla completa: '+('sí' if completa else 'no'),'F11 alterna y conserva el tamaño de ventana',pygame.K_F11),
              ('H','Ayudas en partida: '+('sí' if ayudas else 'no'),'Muestra los atajos básicos junto a la mochila',pygame.K_h),
              ('F2','Ver controles','Todos los atajos, agrupados por acción',pygame.K_F2))
    for i,(tecla,etiqueta,nota,key) in enumerate(opciones):
        rect=(pygame.Rect(margen+(i%2)*(columna+gap),y+(i//2)*(alto+gap),columna,alto) if compacta else
              pygame.Rect(margen,y+i*(alto+gap),ancho,alto))
        boton(sup,rect,tecla,etiqueta,'' if compacta else nota,resaltado=_encima(rect,raton))
        if compacta: _texto.registrar_ayuda(rect,nota)
        hotspots.append((rect,key))
    rect=pygame.Rect(margen,sup.get_height()-p(72), min(p(280),ancho),p(40))
    boton(sup,rect,'Esc','Volver',resaltado=_encima(rect,raton));hotspots.append((rect,pygame.K_ESCAPE))
    _texto.etiqueta(sup,nota_f,'Se recuerda al salir · Tab para elegir · Enter para activar',
                    pygame.Rect(margen,sup.get_height()-24,ancho,nota_f.get_height()),GRIS)
    return hotspots


GRUPOS_CONTROLES=(
    ('EXPLORAR Y COMBATIR',(('WASD / flechas','Caminar por la sala'),('E','Abrir la puerta hacia la que miras'),
      ('Espacio','Atacar al enemigo cercano / objetivo'),('X / Shift+X','Cambiar de objetivo'),
      ('F','Recoger un objeto cercano'),('T','Cambiar selección del suelo'),('U','Rebobinar con un pergamino'))),
    ('MOCHILA, MAPA E HISTORIA',(('Tab / Shift+Tab','Seleccionar objeto (también clic)'),('R / Enter / Q','Usar / equipar / soltar selección'),
      ('C / Shift+C','Cambiar orden de la mochila'),('M','Abrir / cerrar el mapa'),('H','Consultar el historial de la partida'),
      ('Flechas + Enter','Elegir sala del mapa y viajar'),('Esc','Cerrar panel / cancelar viaje'),('Rueda del ratón','Recorrer mochila o panel'))),
    ('OTROS CONTROLES',(('G / Esc','Guardar / pausar la partida'),('F10 / F11','Ajustes / pantalla completa'),
      ('F1','Modo desarrollo'),('Menús','Tab o flechas para elegir; Enter, atajo o clic para activar'))),
)


def _filas_controles(sup):
    m=medidas(sup);f=m.fuente(14);cabecera=m.estilo('h3');tecla=m.fuente(14,peso=600)
    columnas=2 if sup.get_width()>=900 else 1
    ancho=(sup.get_width()-48-24*(columnas-1))//columnas
    filas=[];fondos=[0]*columnas
    for i,(titulo,opciones) in enumerate(GRUPOS_CONTROLES):
        col=i%columnas;y=fondos[col];x=24+col*(ancho+24)
        filas.append((cabecera,titulo,x,y,ancho,DORADO));y+=cabecera.get_linesize()+8
        for combinacion,descripcion in opciones:
            filas.append((tecla,combinacion,x,y,ancho,DORADO));y+=tecla.get_linesize()
            for linea in _texto.envolver(descripcion,f,ancho,100):
                filas.append((f,linea,x,y,ancho,BLANCO));y+=f.get_linesize()
            y+=8
        fondos[col]=y+16
    return filas,max(fondos)


def limite_scroll_controles(sup):
    return max(0,_filas_controles(sup)[1]-(sup.get_height()-160))


def pantalla_controles(sup, fuente, raton=None, desplazamiento=0):
    _fondo_menu(sup);m=medidas(sup);titulo=m.estilo('h1');aux=m.estilo('auxiliar')
    sup.blit(titulo.render('Controles',True,DORADO),(24,16))
    sup.blit(aux.render('↑ ↓ / rueda para desplazar · Tab y Enter para volver',True,GRIS),(24,56))
    area=pygame.Rect(24,80,sup.get_width()-48,sup.get_height()-160)
    anterior=sup.get_clip();sup.set_clip(area)
    filas,alto=_filas_controles(sup);offset=min(limite_scroll_controles(sup),max(0,desplazamiento))
    for fuente,cadena,x,y,ancho,color in filas:
        sup.blit(fuente.render(cadena,True,color),(x,area.y+y-offset))
    sup.set_clip(anterior)
    boton_volver=pygame.Rect(24,sup.get_height()-64, min(280,sup.get_width()-48),40)
    boton(sup,boton_volver,'Esc','Volver',resaltado=_encima(boton_volver,raton))
    if alto>area.h:
        sup.blit(aux.render('Continúa con ↑ ↓ / rueda',True,GRIS),(sup.get_width()-190,sup.get_height()-48))
    return [(boton_volver,pygame.K_ESCAPE)]
