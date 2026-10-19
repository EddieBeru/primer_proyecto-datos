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
from src.view.sprites import (CAJA_ARTE_ALTO, CAJA_ARTE_ANCHO,
                              LID_STAGES, SpriteManager)

if TYPE_CHECKING:  # solo tipos: en runtime la vista solo importa Sesion
    from src.controller2.fachada import FotoEstado

BLANCO = paleta.TEXTO
GRIS = paleta.SECUNDARIO
DORADO = paleta.TITULO
FONDO = paleta.FONDO_APP

FUENTE_FAMILIA = "consolas,monospace"
_FUENTES: dict[tuple[int, bool], pygame.Font] = {}
DAMERO_FONDO = (250, 233, 209)  # damero sutil del fondo de menús

# Tamaños fijos (registro producto: escala consistente, no fluida).
T_DISPLAY, T_TITULO, T_BOTON, T_CUERPO, T_NOTA = 64, 40, 24, 18, 14
CONTROLES = ("WASD/flechas mover · E abrir · Espacio atacar · X objetivo · "
             "F recoger · Tab mochila (Shift atrás) · C orden · Enter equipar · "
             "R usar · Esc pausa")


def _fuente(tam: int, negrita: bool = False) -> pygame.Font:
    clave = (tam, negrita)
    if clave not in _FUENTES:
        _FUENTES[clave] = pygame.font.SysFont(FUENTE_FAMILIA, tam, bold=negrita)
    return _FUENTES[clave]


def _texto_sombra(sup: pygame.Surface, fuente: pygame.Font, texto: str,
                  centro: tuple[int, int], color, sombra=(90, 45, 10)) -> None:
    """Texto con sombra dura: lo hace legible sobre el damero y da peso."""
    etiqueta = fuente.render(texto, True, color)
    x = centro[0] - etiqueta.get_width() // 2
    y = centro[1] - etiqueta.get_height() // 2
    if sombra is not None:
        negativo = fuente.render(texto, True, sombra)
        sup.blit(negativo, (x + 2, y + 2))
    sup.blit(etiqueta, (x, y))


def _fondo_menu(sup: pygame.Surface) -> None:
    """Fondo común: crema + damero sutil, como el piso de la sala."""
    sup.fill(FONDO)
    lado = 40
    for fy in range(0, sup.get_height() // lado):
        for fx in range(0, sup.get_width() // lado):
            if (fx + fy) % 2:
                sup.fill(DAMERO_FONDO,
                         pygame.Rect(fx * lado, fy * lado, lado, lado))


def _panel(sup: pygame.Surface, rect: pygame.Rect,
           fondo=paleta.PANEL, borde=DORADO) -> None:
    """Panel/ tarjeta estándar: rectángulo duro (estética pixel, sin radios)."""
    pygame.draw.rect(sup, fondo, rect)
    pygame.draw.rect(sup, borde, rect, 3)


def _insignia(sup: pygame.Surface, centro: tuple[int, int], numero: str,
              color=DORADO, texto_claro=True) -> None:
    """Cuadrado con la tecla (la interacción se ve de un vistazo).

    Teclas de más de un carácter ("Esc") usan letra más chica para que no
    se salgan del recuadro. Todo a escuadra: nada de círculos.
    """
    lado = 36
    rect = pygame.Rect(0, 0, lado, lado)
    rect.center = centro
    pygame.draw.rect(sup, color, rect)
    pygame.draw.rect(sup, (255, 255, 255), rect, 2)
    fuente = _fuente(T_NOTA, negrita=True) if len(numero) > 1 else _fuente(
        T_CUERPO, negrita=True)
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
    if habilitado and primario:
        fondo, borde, color = DORADO, (150, 60, 0), paleta.TEXTO_CLARO
        if resaltado:
            fondo = (255, 172, 62)
    elif habilitado:
        fondo, borde, color = paleta.PANEL, DORADO, BLANCO
        if resaltado:
            fondo, borde = (252, 228, 198), (160, 70, 0)
    else:
        fondo, borde, color = (238, 228, 214), (185, 170, 150), (150, 138, 122)
    _panel(sup, rect, fondo, borde)
    _insignia(sup, (rect.x + 34, rect.centery), tecla,
              color=(150, 60, 0) if (habilitado and primario) else DORADO,
              texto_claro=habilitado)
    fuente = _fuente(T_BOTON, negrita=True)
    etiqueta_sup = fuente.render(etiqueta, True, color)
    x = rect.x + 62
    y = rect.centery - etiqueta_sup.get_height() // 2
    if nota:
        y -= 9
    sup.blit(etiqueta_sup, (x, y))
    if nota:
        color_nota = (255, 226, 190) if (habilitado and primario) else (
            color if not habilitado else GRIS)
        nota_sup = _fuente(T_NOTA).render(nota, True, color_nota)
        sup.blit(nota_sup, (x, rect.centery + 10))
    return rect


def _prota(sup: pygame.Surface, sprites: SpriteManager | None,
           centro: tuple[int, int], escala: float = 2.0,
           espejo: bool = False, tinte=None) -> None:
    """El prota en grande para los menús.

    Usa el PNG nativo (`jugador_grande`, smoothscale): en partida el sprite
    se reduce a TAM para el look retro, pero en menús esa reducción se veía
    pixelada al agrandarla. `escala` = factor sobre el arte nativo 117×161.
    """
    if sprites is None:
        return
    try:
        img = sprites.jugador_grande(escala, espejo)
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
    try:
        nivel = max(0, min(int(nivel), maximo))
    except (TypeError, ValueError):
        nivel = 0
    lado, hueco = 14, 6
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
    _texto_sombra(sup, _fuente(T_TITULO, negrita=True), texto,
                  (sup.get_width() // 2, y + 16), DORADO)
    return y + 50


def _encima(rect: pygame.Rect, raton: tuple[int, int] | None) -> bool:
    """True si el ratón está sobre el rect (ratón puede no haberse movido)."""
    return raton is not None and rect.collidepoint(raton)


def _pie(sup: pygame.Surface, texto: str) -> None:
    """Línea de ayuda al pie, siempre igual en todos los menús."""
    etiqueta = _fuente(T_NOTA).render(texto, True, GRIS)
    sup.blit(etiqueta, (sup.get_width() // 2 - etiqueta.get_width() // 2,
                        sup.get_height() - 34))


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
    rect = pygame.Rect(
        0, 0, round(CAJA_MENU_ALTO * CAJA_ARTE_ANCHO / CAJA_ARTE_ALTO),
        CAJA_MENU_ALTO)
    rect.midtop = (sup.get_width() // 2, 14)
    return rect


def _caja_menu(sup: pygame.Surface, sprites: SpriteManager | None,
               titulo: str | None = None, color: tuple = DORADO,
               sub: str | None = None,
               stage: int = LID_STAGES) -> pygame.Rect:
    """Caja arriba con el título adentro; retorna su rect.

    Mismo layout en todos los menús (caja arriba, opciones abajo) y mismo
    rect que usa el zoom menú -> partida.
    """
    rect = rect_caja_menu(sup)
    if sprites is not None:
        capas.dibujar_caja_cuerpo(sup, sprites, rect)
    if titulo:
        fuente_t = _fuente(T_BOTON, negrita=True)
        for tam in (T_DISPLAY, T_TITULO, T_BOTON):
            candidata = _fuente(tam, negrita=True)
            if candidata.size(titulo)[0] <= rect.w - 44:
                fuente_t = candidata
                break
        _texto_sombra(sup, fuente_t, titulo, (rect.centerx, rect.centery), color)
    if sub:
        etiqueta = _fuente(T_NOTA).render(sub, True, GRIS)
        sup.blit(etiqueta,
                 etiqueta.get_rect(midtop=(rect.centerx, rect.centery + 40)))
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
    _fondo_menu(sup)
    _caja_menu(sup, sprites, "CRIPTA", sub="explora · saquea · sobrevive",
               stage=stage_caja(apertura))

    # El prota asoma por la derecha, ya sin fondo ni cajas.
    _prota(sup, sprites, (sup.get_width() - 95, 190), 1.2)

    ancho_b, hueco_b = 250, 25
    x0 = sup.get_width() // 2 - (3 * ancho_b + 2 * hueco_b) // 2
    rects = [
        pygame.Rect(x0, 530, ancho_b, 74),
        pygame.Rect(x0 + ancho_b + hueco_b, 530, ancho_b, 74),
        pygame.Rect(x0 + 2 * (ancho_b + hueco_b), 530, ancho_b, 74),
    ]
    boton(sup, rects[0], "1", "Jugar", "elige tu cripta", primario=True,
          resaltado=_encima(rects[0], raton))
    boton(sup, rects[1], "2", "Continuar",
          "partida guardada" if puede_continuar else "sin guardado aún",
          habilitado=puede_continuar, resaltado=_encima(rects[1], raton))
    boton(sup, rects[2], "3", "Salir", "", resaltado=_encima(rects[2], raton))
    _pie(sup, "pulsa el número o haz clic en la opción")
    hotspots = [(rects[0], pygame.K_1)]
    if puede_continuar:
        hotspots.append((rects[1], pygame.K_2))
    hotspots.append((rects[2], pygame.K_3))
    return hotspots


def _tarjeta_cripta(sup: pygame.Surface, rect: pygame.Rect, numero: int,
                    nombre: str, salas, dificultad,
                    resaltada: bool = False) -> None:
    """Tarjeta compacta de cripta: número, nombre, salas y picante."""
    _panel(sup, rect, (252, 228, 198) if resaltada else paleta.PANEL,
           (160, 70, 0) if resaltada else DORADO)
    _insignia(sup, (rect.x + 30, rect.centery), str(numero))
    fuente_nombre = _fuente(T_CUERPO, negrita=True)
    lineas = _texto.envolver(nombre, fuente_nombre, rect.w - 160,
                             2 if rect.h >= 74 else 1)
    y = rect.centery - len(lineas) * 11
    for parte in lineas:
        sup.blit(fuente_nombre.render(parte, True, BLANCO), (rect.x + 58, y))
        y += 22
    # Salas: puerta a escuadra + número.
    pygame.draw.rect(sup, paleta.MURO,
                     pygame.Rect(rect.x + 58, rect.bottom - 28, 14, 18))
    pygame.draw.rect(sup, paleta.PUERTA_ABIERTA,
                     pygame.Rect(rect.x + 61, rect.bottom - 25, 8, 12))
    sup.blit(_fuente(T_NOTA).render(f"{salas} salas", True, GRIS),
             (rect.x + 78, rect.bottom - 27))
    _puntos_dificultad(sup, rect.right - 104, rect.bottom - 19, dificultad)


def pantalla_seleccion(sup: pygame.Surface, fuente: pygame.Font,
                       criptas: list,
                       sprites: SpriteManager | None = None,
                       raton: tuple[int, int] | None = None
                       ) -> list[tuple[pygame.Rect, int]]:
    """1.2 Tarjetas de cripta bajo la caja: elegir de un vistazo."""
    _fondo_menu(sup)
    rect_caja = _caja_menu(sup, sprites, "Elige tu cripta",
                           sub="pulsa el número de la cripta · Esc vuelve")
    total = max(len(criptas), 1)
    columnas = 2 if total <= 4 else 3
    hueco = 12
    ancho = (sup.get_width() - 40 - hueco * (columnas - 1)) // columnas
    filas = (total + columnas - 1) // columnas
    y0 = rect_caja.bottom + 18
    disponible = sup.get_height() - 40 - y0
    alto = max(54, min(92, (disponible - hueco * (filas - 1)) // filas))
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
    etiqueta = _fuente(T_BOTON, negrita=True).render(detalle, True, BLANCO)
    sup.blit(etiqueta, (sup.get_width() // 2 - etiqueta.get_width() // 2,
                        cy + 48))


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
                   criterio_inv: str | None = None) -> None:
    """1.4 Sala + actores + HUD. Toda la lectura sale de la foto.

    `orden_inv`/`criterio_inv`: copia ordenada de la mochila ya calculada
    por la Sesión (§4.5); la vista solo la dibuja, nunca ordena.

    Distribución: canvas arriba centrado (4 partes) y banda de información
    abajo (1 parte): contadores en una línea y mochila horizontal debajo.
    """
    sup.fill(FONDO)
    titulo = fuente.render(f"Sala {foto.sala_id}: {foto.sala_nombre} [{foto.estado}]",
                           True, DORADO)
    sup.blit(titulo, titulo.get_rect(midtop=(area_sala.centerx, 8)))
    pygame.draw.line(sup, DORADO, (10, 30),
                     (sup.get_width() - 10, 30), 2)
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
    # La línea de HUD va bajo la caja (arte con padding), no bajo el área.
    linea = capas.rect_caja(area_sala).bottom + 2
    pygame.draw.line(sup, DORADO, (8, linea), (sup.get_width() - 8, linea), 2)
    zona = pygame.Rect(14, linea + 4, sup.get_width() - 28,
                       sup.get_height() - linea - 10)
    ui.dibujar_contadores(sup, fuente, zona, foto, dev)
    ui.dibujar_mochila(sup, fuente,
                       pygame.Rect(zona.x, zona.y + 30, zona.w, zona.h - 30),
                       foto, sprites, sel_inv, orden=orden_inv,
                       sufijo_orden=f" (por {criterio_inv})" if criterio_inv else None)
    controles = _fuente(T_NOTA).render(CONTROLES, True, GRIS)
    sup.blit(controles,
             controles.get_rect(midbottom=(zona.centerx, zona.bottom - 2)))
    ui.dibujar_toast(sup, fuente, foto.error or "", tope_inferior=linea - 4)


def _resumen_final(sup: pygame.Surface, rect: pygame.Rect, foto: "FotoEstado",
                   reporte: dict | None) -> int:
    """Filas etiqueta -> valor del resumen final. Retorna la y final.

    Si el valor no cabe a la derecha de la etiqueta, baja a su propia
    línea (nombres de sala largos, rutas…): nunca se solapan.
    """
    filas = [
        ("Sala alcanzada", f"{foto.sala_id} — {foto.sala_nombre}"),
        ("Pergaminos", str(foto.pergaminos)),
        ("Puntos de vida", str(foto.jugador.get("vida", "?"))),
    ]
    if reporte and reporte.get("terminada") and reporte.get("red"):
        red = reporte["red"]
        filas.insert(2, ("Peticiones a la cripta",
                         f"{red.get('realizadas', '?')} de {red.get('presupuesto', '?')}"))

    fuente_et = _fuente(T_CUERPO)
    fuente_val = _fuente(T_CUERPO, negrita=True)
    y = rect.y + 14
    x_izq, x_der = rect.x + 20, rect.right - 20
    for etiqueta, valor in filas:
        izq = fuente_et.render(etiqueta, True, GRIS)
        der = fuente_val.render(str(valor), True, BLANCO)
        cabe = x_izq + izq.get_width() + 16 + der.get_width() <= x_der
        sup.blit(izq, (x_izq, y))
        if cabe:
            sup.blit(der, (x_der - der.get_width(), y))
            y += 28
        else:
            y += 24
            sup.blit(der, (x_izq + 10, y))
            y += 30
        pygame.draw.line(sup, (232, 214, 190),
                         (x_izq, y - 6), (x_der, y - 6))
    return y


def pantalla_fin(sup: pygame.Surface, fuente: pygame.Font, foto: "FotoEstado",
                 reporte: dict | None = None,
                 sprites: SpriteManager | None = None,
                 raton: tuple[int, int] | None = None
                 ) -> list[tuple[pygame.Rect, int]]:
    """1.5 Victoria / derrota: caja arriba, resumen y acciones abajo (guía §9)."""
    _fondo_menu(sup)
    gano = foto.estado == "victoria"
    color = paleta.VIDA if gano else paleta.PELIGRO
    rect_caja = _caja_menu(sup, sprites, "¡VICTORIA!" if gano else "DERROTA",
                           color=color,
                           sub="escapaste con el botín" if gano
                           else "la cripta te venció… esta vez")

    y_fila = rect_caja.bottom + 26
    # El prota (rojo si cayó), con el botín al ganar.
    _prota(sup, sprites, (150, y_fila + 100), 1.2,
           tinte=None if gano else (255, 120, 120))
    if gano:
        _adorno(sup, sprites, "escudo", (64, y_fila + 60), 2)
        _adorno(sup, sprites, "espada", (238, y_fila + 56), 2)

    # Resumen con datos legibles (nada de diccionarios crudos).
    rect = pygame.Rect(sup.get_width() - 40 - 372, y_fila, 372, 210)
    _panel(sup, rect)
    _resumen_final(sup, rect, foto, reporte)

    # Últimos sucesos humanizados + pie técnico en la columna central.
    x_col, ancho_col = 300, 250
    y = y_fila + 8
    for linea in [_texto.humanizar(m) for m in (foto.mensajes or [])[-3:]]:
        for parte in _texto.envolver(linea, fuente, ancho_col, 1):
            sup.blit(fuente.render(parte, True, GRIS), (x_col, y))
            y += 18
    if reporte and reporte.get("puntajes_ruta"):
        for parte in _texto.envolver(f"puntajes: {reporte['puntajes_ruta']}",
                                     fuente, ancho_col, 1):
            sup.blit(fuente.render(parte, True, (180, 158, 136)), (x_col, y))
            y += 18
    if reporte and reporte.get("puntaje_error"):
        error = f"no se guardó el puntaje: {reporte['puntaje_error']}"
        for parte in _texto.envolver(error, fuente, ancho_col, 2):
            sup.blit(fuente.render(parte, True, paleta.PELIGRO), (x_col, y))
            y += 18

    ancho_b, hueco_b = 410, 20
    x0 = sup.get_width() // 2 - (2 * ancho_b + hueco_b) // 2
    y_b = sup.get_height() - 100
    b1 = pygame.Rect(x0, y_b, ancho_b, 60)
    b2 = pygame.Rect(x0 + ancho_b + hueco_b, y_b, ancho_b, 60)
    boton(sup, b1, "1", "Jugar de nuevo", "otra partida de la misma cripta",
          primario=True, resaltado=_encima(b1, raton))
    boton(sup, b2, "2", "Volver al menú", "", resaltado=_encima(b2, raton))
    return [(b1, pygame.K_1), (b2, pygame.K_2)]


def pantalla_error(sup: pygame.Surface, fuente: pygame.Font, mensaje: str,
                   sprites: SpriteManager | None = None,
                   raton: tuple[int, int] | None = None
                   ) -> list[tuple[pygame.Rect, int]]:
    """1.6 Error amable a pantalla completa (red, presupuesto, guardado)."""
    sup.fill(paleta.PELIGRO_FONDO)
    rect_caja = _caja_menu(sup, sprites, "Algo salió mal",
                           color=paleta.TEXTO_CLARO,
                           sub="tu partida sigue a salvo")
    fuente_cuerpo = _fuente(T_CUERPO)
    y = rect_caja.bottom + 26
    for parte in _texto.envolver(mensaje, fuente_cuerpo,
                                 sup.get_width() - 160, 4):
        sup.blit(fuente_cuerpo.render(parte, True, paleta.TEXTO_CLARO),
                 (80, y))
        y += 24
    boton_volver = pygame.Rect(0, 0, 340, 56)
    boton_volver.midtop = (sup.get_width() // 2, y + 10)
    boton(sup, boton_volver, "Esc", "Volver al menú", "",
          resaltado=_encima(boton_volver, raton))
    _pie(sup, "Esc o el botón vuelven al menú")
    return [(boton_volver, pygame.K_ESCAPE)]


def pantalla_version(sup: pygame.Surface, fuente: pygame.Font, mensaje: str,
                     sprites: SpriteManager | None = None,
                     raton: tuple[int, int] | None = None
                     ) -> list[tuple[pygame.Rect, int]]:
    """1.7 Partida de versión anterior: nunca cargar a medias (guía §9)."""
    _fondo_menu(sup)
    rect_caja = _caja_menu(sup, sprites, "Versión anterior",
                           sub="tu guardado no se cargó a medias")
    fuente_cuerpo = _fuente(T_CUERPO)
    y = rect_caja.bottom + 26
    for parte in _texto.envolver(mensaje, fuente_cuerpo,
                                 sup.get_width() - 160, 4):
        sup.blit(fuente_cuerpo.render(parte, True, BLANCO), (80, y))
        y += 24
    boton_volver = pygame.Rect(0, 0, 340, 56)
    boton_volver.midtop = (sup.get_width() // 2, y + 10)
    boton(sup, boton_volver, "Esc", "Volver al menú", "",
          resaltado=_encima(boton_volver, raton))
    _pie(sup, "Esc o el botón vuelven al menú")
    return [(boton_volver, pygame.K_ESCAPE)]


def menu_pausa(sup: pygame.Surface, fuente: pygame.Font,
               sprites: SpriteManager | None = None,
               raton: tuple[int, int] | None = None
               ) -> list[tuple[pygame.Rect, int]]:
    """Pausa (Esc): menú local; guardar/cargar/salir vía Sesión en el App."""
    _fondo_menu(sup)
    rect_caja = _caja_menu(sup, sprites, "Pausa")
    ancho, alto = 460, 52
    x = sup.get_width() // 2 - ancho // 2
    y = rect_caja.bottom + 16
    hotspots: list[tuple[pygame.Rect, int]] = []
    for tecla, etiqueta, nota, codigo in (
            ("G", "Guardar", "guarda la partida actual", pygame.K_g),
            ("C", "Cargar", "retoma el último guardado", pygame.K_c),
            ("Esc", "Volver", "sigue jugando", pygame.K_ESCAPE),
            ("Q", "Salir al menú", "no pierde el guardado", pygame.K_q)):
        rect = pygame.Rect(x, y, ancho, alto)
        boton(sup, rect, tecla, etiqueta, nota,
              resaltado=_encima(rect, raton))
        hotspots.append((rect, codigo))
        y += alto + 10
    return hotspots
