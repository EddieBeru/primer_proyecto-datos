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
from src.view.sprites import SpriteManager

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
          nota: str = "", primario: bool = False, habilitado: bool = True) -> None:
    """Botón de menú: insignia de tecla + etiqueta + nota secundaria.

    `primario` (acción principal) va en naranja lleno; el resto en panel
    claro con borde. Deshabilitado: gris y nota visible (no se oculta).
    """
    if habilitado and primario:
        fondo, borde, color = DORADO, (150, 60, 0), paleta.TEXTO_CLARO
    elif habilitado:
        fondo, borde, color = paleta.PANEL, DORADO, BLANCO
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


def _prota(sup: pygame.Surface, sprites: SpriteManager | None,
           centro: tuple[int, int], escala: int = 3,
           espejo: bool = False, tinte=None) -> None:
    """El prota en grande para los menús (frame quieto, sin implementos)."""
    if sprites is None:
        return
    try:
        img, _ = sprites.jugador_frame(False, 0, "S", 0, espejo=espejo)
    except Exception:
        img = sprites.icono()
        if espejo:
            img = pygame.transform.flip(img, True, False)
    img = pygame.transform.scale(
        img, (img.get_width() * escala, img.get_height() * escala))
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


def _pie(sup: pygame.Surface, texto: str) -> None:
    """Línea de ayuda al pie, siempre igual en todos los menús."""
    etiqueta = _fuente(T_NOTA).render(texto, True, GRIS)
    sup.blit(etiqueta, (sup.get_width() // 2 - etiqueta.get_width() // 2,
                        sup.get_height() - 34))


def pantalla_inicio(sup: pygame.Surface, fuente: pygame.Font,
                    puede_continuar: bool,
                    sprites: SpriteManager | None = None) -> None:
    """1.1 Menú: logo + prota + tres botones con tecla visible."""
    _fondo_menu(sup)
    # Logo flanqueado por el escudo-pizza y la espada-pizza (arte del juego).
    _adorno(sup, sprites, "escudo", (300, 104), 2)
    _adorno(sup, sprites, "espada", (692, 100), 2)
    _texto_sombra(sup, _fuente(T_DISPLAY, negrita=True), "CRIPTA",
                  (sup.get_width() // 2, 104), DORADO)
    sub = _fuente(T_CUERPO).render("explora · saquea · sobrevive", True, GRIS)
    sup.blit(sub, (sup.get_width() // 2 - sub.get_width() // 2, 152))

    # El prota mira los botones (arte grande, sin fondos ni cajas).
    _prota(sup, sprites, (796, 396), 4, espejo=True)

    rects = [
        pygame.Rect(120, 240, 460, 74),
        pygame.Rect(120, 334, 460, 74),
        pygame.Rect(120, 428, 460, 74),
    ]
    boton(sup, rects[0], "1", "Jugar", "elige tu cripta", primario=True)
    boton(sup, rects[1], "2", "Continuar partida",
          "" if puede_continuar else "sin guardado todavía",
          habilitado=puede_continuar)
    boton(sup, rects[2], "3", "Salir", "")
    _pie(sup, "pulsa el número de la opción")


def pantalla_seleccion(sup: pygame.Surface, fuente: pygame.Font,
                       criptas: list,
                       sprites: SpriteManager | None = None) -> None:
    """1.2 Tarjetas de cripta: nombre grande, salas y dificultad dibujadas."""
    _fondo_menu(sup)
    _texto_sombra(sup, _fuente(T_TITULO, negrita=True), "Elige tu cripta",
                  (sup.get_width() // 2, 62), DORADO)
    sub = _fuente(T_CUERPO).render("pulsa el número de la cripta · Esc vuelve",
                                   True, GRIS)
    sup.blit(sub, (sup.get_width() // 2 - sub.get_width() // 2, 108))

    total = max(len(criptas), 1)
    columnas = 2 if total <= 4 else 3
    ancho = 400 if columnas == 2 else 272
    alto = 128
    hueco_x, hueco_y = 32, 28
    ancho_total = columnas * ancho + (columnas - 1) * hueco_x
    x0 = sup.get_width() // 2 - ancho_total // 2
    y0 = 168
    for i, cripta in enumerate(criptas):
        fila, col = divmod(i, columnas)
        rect = pygame.Rect(x0 + col * (ancho + hueco_x),
                           y0 + fila * (alto + hueco_y), ancho, alto)
        nombre = str(cripta.get("nombre", cripta.get("id", "?")))
        salas = cripta.get("salas", "?")
        dificultad = cripta.get("dificultad", 0)
        _panel(sup, rect)
        _insignia(sup, (rect.x + 38, rect.y + 38), str(i + 1))
        # Nombre (hasta 2 líneas).
        fuente_nombre = _fuente(T_BOTON, negrita=True)
        for k, parte in enumerate(_texto.envolver(nombre, fuente_nombre,
                                                  ancho - 90, 2)):
            sup.blit(fuente_nombre.render(parte, True, BLANCO),
                     (rect.x + 68, rect.y + 20 + k * 26))
        # Salas: puerta dibujada (a escuadra) + número.
        pygame.draw.rect(sup, paleta.MURO,
                         pygame.Rect(rect.x + 24, rect.bottom - 52, 22, 30))
        pygame.draw.rect(sup, paleta.PUERTA_ABIERTA,
                         pygame.Rect(rect.x + 27, rect.bottom - 49, 16, 24))
        salas_sup = _fuente(T_CUERPO, negrita=True).render(
            f"{salas} salas", True, BLANCO)
        sup.blit(salas_sup, (rect.x + 54, rect.bottom - 48))
        # Dificultad: pepperoni (5 puntos).
        etiqueta = _fuente(T_NOTA).render("picante", True, GRIS)
        sup.blit(etiqueta, (rect.right - 200, rect.bottom - 46))
        _puntos_dificultad(sup, rect.right - 130, rect.bottom - 38,
                           dificultad)
    _pie(sup, "1-9 elige · Esc vuelve al menú")


def pantalla_carga(sup: pygame.Surface, fuente: pygame.Font,
                   detalle: str = "Preparando la cripta…") -> None:
    """1.3 Carga + aviso 429 («esperando N s…», guía §5: sin congelar)."""
    _fondo_menu(sup)
    cx, cy = sup.get_width() // 2, sup.get_height() // 2
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
                   trampas_fuego: dict[str, float] | None = None) -> None:
    """1.4 Sala + actores + HUD. Toda la lectura sale de la foto."""
    sup.fill(FONDO)
    titulo = fuente.render(f"Sala {foto.sala_id}: {foto.sala_nombre} [{foto.estado}]",
                           True, DORADO)
    sup.blit(titulo, (10, 8))
    pygame.draw.line(sup, DORADO, (10, 30),
                     (sup.get_width() - 10, 30), 2)
    capas.dibujar_fondo(sup, area_sala, foto, sprites, fuente)
    capas.dibujar_estatica(sup, area_sala, foto, sprites, sel_suelo, fuente,
                           spots, trampas_fuego)
    capas.dibujar_actores(sup, area_sala, foto, sprites, fuente,
                          sel_enemigo, ref_vida, facing, desplaza, paso_jugador,
                          pos_jugador, golpe, alcance,
                          tinte_dano, tajo, espejo)
    # Mejoras 2026-10: sala oscura -> velo con halo (o luz plena con antorcha).
    capas.dibujar_oscuridad(sup, area_sala, foto, pos_jugador)
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
                 sprites: SpriteManager | None = None) -> None:
    """1.5 Victoria / derrota: arte + resumen + acciones (guía §9)."""
    _fondo_menu(sup)
    gano = foto.estado == "victoria"
    titulo = "¡VICTORIA!" if gano else "DERROTA"
    color = paleta.VIDA if gano else paleta.PELIGRO
    _texto_sombra(sup, _fuente(T_TITULO, negrita=True), titulo,
                  (sup.get_width() // 2, 58), color)
    sub = "escapaste con el botín" if gano else "la cripta te venció… esta vez"
    etiqueta = _fuente(T_CUERPO).render(sub, True, GRIS)
    sup.blit(etiqueta, (sup.get_width() // 2 - etiqueta.get_width() // 2, 96))

    # Arte: el prota (rojo si cayó), más escudo y espada como botín tras ganar.
    _prota(sup, sprites, (330, 300), 3,
           tinte=None if gano else (255, 120, 120))
    if gano:
        _adorno(sup, sprites, "escudo", (238, 236), 2)
        _adorno(sup, sprites, "espada", (428, 236), 2)

    # Resumen con datos legibles (nada de diccionarios crudos).
    rect = pygame.Rect(576, 140, 348, 240)
    _panel(sup, rect)
    y = _resumen_final(sup, rect, foto, reporte)

    # Últimos sucesos, humanizados + pie técnico, siempre dentro de la columna.
    eventos = [_texto.humanizar(m) for m in (foto.mensajes or [])[-3:]]
    y = max(y, rect.bottom) + 10
    for linea in eventos:
        for parte in _texto.envolver(linea, fuente, rect.w - 40, 1):
            sup.blit(fuente.render(parte, True, GRIS), (rect.x + 20, y))
            y += 18
    if reporte and reporte.get("puntajes_ruta"):
        for parte in _texto.envolver(f"puntajes: {reporte['puntajes_ruta']}",
                                     fuente, rect.w - 40, 1):
            sup.blit(fuente.render(parte, True, (180, 158, 136)),
                     (rect.x + 20, y))
            y += 18
    if reporte and reporte.get("puntaje_error"):
        error = f"no se guardó el puntaje: {reporte['puntaje_error']}"
        for parte in _texto.envolver(error, fuente, rect.w - 40, 2):
            sup.blit(fuente.render(parte, True, paleta.PELIGRO),
                     (rect.x + 20, y))
            y += 18

    boton(sup, pygame.Rect(120, 430, 460, 68), "1", "Jugar de nuevo",
          "otra partida de la misma cripta", primario=True)
    boton(sup, pygame.Rect(120, 510, 460, 68), "2", "Volver al menú", "")
    _pie(sup, "1 nueva partida · 2 menú · Esc menú")


def pantalla_error(sup: pygame.Surface, fuente: pygame.Font, mensaje: str) -> None:
    """1.6 Error amable a pantalla completa (red, presupuesto, guardado)."""
    sup.fill(paleta.PELIGRO_FONDO)
    _texto_sombra(sup, _fuente(T_TITULO, negrita=True),
                  "Algo salió mal", (sup.get_width() // 2, 70),
                  paleta.TEXTO_CLARO, sombra=(60, 10, 5))
    sub = _fuente(T_CUERPO).render("tu partida sigue a salvo", True,
                                   (255, 214, 200))
    sup.blit(sub, (sup.get_width() // 2 - sub.get_width() // 2, 104))
    y = 190
    fuente_cuerpo = _fuente(T_CUERPO)
    for parte in _texto.envolver(mensaje, fuente_cuerpo, sup.get_width() - 160, 4):
        sup.blit(fuente_cuerpo.render(parte, True, paleta.TEXTO_CLARO),
                 (80, y))
        y += 24
    _pie(sup, "Esc vuelve al menú")


def pantalla_version(sup: pygame.Surface, fuente: pygame.Font, mensaje: str) -> None:
    """1.7 Partida de versión anterior: nunca cargar a medias (guía §9)."""
    _fondo_menu(sup)
    _texto_sombra(sup, _fuente(T_TITULO, negrita=True), "Versión anterior",
                  (sup.get_width() // 2, 70), DORADO)
    sub = _fuente(T_CUERPO).render(
        "tu guardado es de otra versión; no se cargó a medias", True, GRIS)
    sup.blit(sub, (sup.get_width() // 2 - sub.get_width() // 2, 104))
    y = 190
    fuente_cuerpo = _fuente(T_CUERPO)
    for parte in _texto.envolver(mensaje, fuente_cuerpo, sup.get_width() - 160, 4):
        sup.blit(fuente_cuerpo.render(parte, True, BLANCO), (80, y))
        y += 24
    _pie(sup, "Esc vuelve al menú")


def menu_pausa(sup: pygame.Surface, fuente: pygame.Font) -> None:
    """Pausa (Esc): menú local; guardar/cargar/salir vía Sesión en el App."""
    _fondo_menu(sup)
    _texto_sombra(sup, _fuente(T_TITULO, negrita=True), "Pausa",
                  (sup.get_width() // 2, 92), DORADO)
    ancho, alto = 380, 60
    x = sup.get_width() // 2 - ancho // 2
    y = 190
    for tecla, etiqueta, nota in (
            ("G", "Guardar", "guarda la partida actual"),
            ("C", "Cargar", "retoma el último guardado"),
            ("Esc", "Volver", "sigue jugando"),
            ("Q", "Salir al menú", "no pierde el guardado")):
        boton(sup, pygame.Rect(x, y, ancho, alto), tecla, etiqueta, nota)
        y += alto + 14
