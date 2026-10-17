"""Las cuatro capas de dibujo (Parte 1 §2): fondo, estática, actores.

La UI (4ta capa) vive en `ui.py`. Cada función recibe la foto (solo lectura)
y dibuja sin mutarla. Direcciones N/S/E/O; ausente = muro, no puerta.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.view import paleta
from src.view import texto as _texto
from src.view.sprites import TAM, SpriteManager, clase_de_id

if TYPE_CHECKING:  # solo tipos: en runtime la vista solo importa Sesion
    from src.controller2.fachada import FotoEstado

FONDO_SALA = paleta.FONDO_SALA
MURO = paleta.MURO

# Posición de cada puerta dentro del área de sala (N arriba, etc.).
POS_PUERTA = {"N": (0.5, 0.0), "S": (0.5, 1.0), "E": (1.0, 0.5), "O": (0.0, 0.5)}

RADIO_PUERTA = 40  # px para cruzar/recibir aviso
RADIO_OBJETO = 56  # px para recoger del suelo
RADIO_ENEMIGO = 80  # px para atacar (generoso: el aviso solo si lejos)

# Escudo fijo al centro vertical (si sube/baja tapa cabeza/pies);
# solo se desplaza en horizontal según hacia dónde mira.
OFFSET_ESCUDO = {"N": (0, 0), "S": (0, 0), "E": (12, 0), "O": (-12, 0)}

# Espada cerca de las manos (costado bajo del cuerpo); separada del escudo
# para que ambos equipos se lean a la vez. Nunca tapa la cara.
OFFSET_ESPADA = {"N":(21, 0), "S": (21, 0), "E": (21, 0), "O": (-21, 0)}


def armadura_visible(foto) -> bool:
    """Hay armadura puesta (foto nueva o equipado frontal por clase)."""
    if getattr(foto, "armadura_equipada", None):
        return True
    equipado = getattr(foto, "equipado", None)
    return bool(equipado) and clase_de_id(equipado) == "armadura"


def arma_visible(foto) -> bool:
    """Hay arma puesta (foto nueva o equipado frontal por clase)."""
    if getattr(foto, "arma_equipada", None):
        return True
    equipado = getattr(foto, "equipado", None)
    return bool(equipado) and clase_de_id(equipado) == "arma"


def rect_puerta(area: pygame.Rect, direccion: str) -> pygame.Rect:
    """Rect de la puerta (misma geometría que dibujar_fondo)."""
    fx, fy = POS_PUERTA[direccion]
    x = area.x + int(fx * (area.w - TAM)) + (0 if fx in (0.0, 1.0) else 0)
    y = area.y + int(fy * (area.h - TAM))
    return pygame.Rect(x, y, TAM, TAM)


SPOTS_COLS = 6  # retícula base de puestos estáticos (columnas)
SPOTS_FILAS = 4  # retícula base de puestos estáticos (filas)
SPOT_JITTER = 22  # desvío determinista del puesto (px)
SPOT_MARGEN = 36  # margen al borde del área para el centro del puesto


def banda_enemiga(area: pygame.Rect) -> pygame.Rect:
    """Zona donde dibujan los enemigos (rejilla 4x2); los puestos la esquivan."""
    return pygame.Rect(area.centerx - 116, area.centery - 60, 232, 120)


def _jitter(k: int) -> tuple[int, int]:
    """Desvío pseudoaleatorio fijo del puesto k: mismo tablero en cada sala."""
    r = (1103515245 * (k * 3 + 7) + 12345) & 0x7FFFFFFF
    dx = r % (2 * SPOT_JITTER + 1) - SPOT_JITTER
    r = (1103515245 * (r >> 7) + 12345) & 0x7FFFFFFF
    dy = r % (2 * SPOT_JITTER + 1) - SPOT_JITTER
    return dx, dy


def spots_estaticos(area: pygame.Rect) -> list[tuple[int, int]]:
    """Puestos con jitter fijo repartidos por el área.

    Descarta los que pisan alguna puerta (con margen) o la banda enemiga.
    """
    x0, x1 = area.x + SPOT_MARGEN, area.right - SPOT_MARGEN
    y0, y1 = area.y + SPOT_MARGEN, area.bottom - SPOT_MARGEN
    excluir = [rect_puerta(area, d).inflate(28, 28) for d in POS_PUERTA]
    excluir.append(banda_enemiga(area))
    libres: list[tuple[int, int]] = []
    for k in range(SPOTS_COLS * SPOTS_FILAS):
        col, fila = k % SPOTS_COLS, k // SPOTS_COLS
        dx, dy = _jitter(k)
        x = x0 + (x1 - x0) * col // max(1, SPOTS_COLS - 1) + dx
        y = y0 + (y1 - y0) * fila // max(1, SPOTS_FILAS - 1) + dy
        tile = pygame.Rect(x - TAM // 2, y - TAM // 2, TAM, TAM)
        if area.contains(tile) and not any(tile.colliderect(e) for e in excluir):
            libres.append((x, y))
    return libres or [(area.centerx, area.centery)]


def _hash_slot(texto: str, n: int) -> int:
    """FNV-1a: estable entre procesos (``hash()`` cambia con PYTHONHASHSEED)."""
    h = 2166136261
    for b in texto.encode("utf-8"):
        h = ((h ^ b) * 16777619) & 0xFFFFFFFF
    return h % max(1, n)


def _ident(x, i: int) -> str:
    if isinstance(x, dict):
        return str(x.get("instancia", f"t{i}"))
    return str(x)


def asignar_spots(area: pygame.Rect, sala: int, trampas, items,
                  memoria: dict | None = None) -> tuple[list, list]:
    """Puntos (items, trampas) estables por identidad, en orden de entrada.

    ``crc32(sala|tipo|id)`` elige puesto; si está ocupado prueba el siguiente
    libre. ``memoria`` congela la asignación de la sesión: recoger o soltar
    nunca mueve a los demás. Sin memoria el resultado es el mismo para el
    mismo contenido (recarga/reinicio reproducible).
    """
    spots = spots_estaticos(area)
    n = len(spots)
    memoria = memoria if memoria is not None else {}
    usados: set[int] = set()
    vistos: dict[tuple, int] = {}
    out: dict[str, list] = {"item": [], "trampa": []}
    for tipo, lista in (("trampa", list(trampas or [])), ("item", list(items or []))):
        for i, bruto in enumerate(lista):
            ident = _ident(bruto, i)
            base = (sala, tipo, ident)
            k = vistos.get(base, 0)
            vistos[base] = k + 1
            clave = base + (k,)
            slot = memoria.get(clave)
            if slot is None or slot in usados:
                inicio = _hash_slot(f"{sala}|{tipo}|{ident}|{k}", n)
                slot = next(((inicio + d) % n for d in range(n)
                             if (inicio + d) % n not in usados), inicio)
            usados.add(slot)
            memoria[clave] = slot
            out[tipo].append(spots[slot])
    return out["item"], out["trampa"]


def pos_enemigo(area: pygame.Rect, i: int) -> tuple[int, int]:
    """Centro del slot del i-ésimo enemigo vivo (misma geometría que dibujar).

    Rejilla centrada 4x2 (hasta 8): ningún slot tapa las puertas N/S/E/O.
    """
    sep = TAM + 20
    col = i % 4
    fila = (i // 4) % 2
    x = area.centerx + (col * 2 - 3) * sep // 2
    y = area.centery + (fila * 2 - 1) * 28
    return x, y


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
                  sprites: SpriteManager, fuente: pygame.Font | None = None) -> None:
    """Capa 1: piso damero + puertas (inexistente/abierta/cerrada-llave/trabada).

    Puerta abierta con cierre programado: badge con ticks restantes.
    """
    sup.fill(FONDO_SALA, area)
    paso = 24
    for yy in range(area.y, area.y + area.h, paso):
        for xx in range(area.x, area.x + area.w, paso):
            if ((xx - area.x) // paso + (yy - area.y) // paso) % 2:
                sup.fill(paleta.PISO_ALT, pygame.Rect(xx, yy, paso, paso))
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
            pygame.draw.circle(sup, paleta.LLAVE_PUNTO, (x + TAM // 2, y + TAM // 2), 5)
        cierre = puerta.get("cierre_en")
        if fuente is not None and cierre is not None and not puerta.get("cerrada"):
            # Badge ASCII (la fuente no trae emojis): ticks restantes.
            etiqueta = fuente.render(f"{cierre}t", True, paleta.TITULO)
            fondo = pygame.Rect(x - 4, y + TAM + 2, etiqueta.get_width() + 8, 18)
            sup.fill(paleta.MURO, fondo)
            sup.blit(etiqueta, (x, y + TAM + 2))


def dibujar_estatica(sup: pygame.Surface, area: pygame.Rect, foto: "FotoEstado",
                     sprites: SpriteManager, sel_suelo: int = 0,
                     fuente: pygame.Font | None = None,
                     spots: tuple[list, list] | None = None) -> None:
    """Capa 2: objetos del suelo + trampas (armada vs desactivada).

    ``spots`` = (items, trampas) ya asignados; None = calcular sin memoria.
    """
    suelo = list(foto.objetos_suelo or [])
    trampas = list(foto.trampas or [])
    if spots is None:
        spots = asignar_spots(area, foto.sala_id, trampas, suelo)
    puntos_items, puntos_trampas = spots
    for i, item_id in enumerate(suelo):
        cx, cy = puntos_items[i]
        x, y = cx - TAM // 2, cy - TAM // 2
        sup.blit(sprites.sprite(item_id), (x, y))
        if i == sel_suelo % max(len(suelo), 1):
            pygame.draw.rect(sup, paleta.TITULO, pygame.Rect(x, y, TAM, TAM), 2)
            etiqueta = fuente.render(_texto.etiqueta_item(item_id), True, paleta.TEXTO) \
                if fuente is not None else None
            if etiqueta is not None:
                fondo = pygame.Rect(x, y + TAM + 2, etiqueta.get_width() + 4, 18)
                sup.fill(paleta.ETIQUETA_FONDO, fondo)
                sup.blit(etiqueta, (x + 2, y + TAM + 2))
    for j, trampa in enumerate(trampas):
        cx, cy = puntos_trampas[j]
        x, y = cx - TAM // 2, cy - TAM // 2
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
    if armadura_visible(foto):  # escudo encima, hacia donde mira
        esc = sprites.escudo()
        dx, dy = OFFSET_ESCUDO.get(facing, (0, 0))
        cx = jx + img_jugador.get_width() // 2 + dx
        cy = jy + img_jugador.get_height() // 2 + dy
        sup.blit(esc, (cx - esc.get_width() // 2, cy - esc.get_height() // 2))
    if arma_visible(foto):  # espada rotada cerca de las manos, sobre todo
        esp = sprites.espada(facing)
        dx, dy = OFFSET_ESPADA.get(facing, (17, 10))
        cx = jx + img_jugador.get_width() // 2 + dx
        cy = jy + img_jugador.get_height() // 2 + dy
        sup.blit(esp, (cx - esp.get_width() // 2, cy - esp.get_height() // 2))
    vivos = [e for e in (foto.enemigos or []) if e.get("vida", 0) > 0]
    for i, enemigo in enumerate(vivos):
        cx, cy = pos_enemigo_animada(area, i, total)
        img = sprites.enemigo(str(enemigo.get("comportamiento", "")))
        sup.blit(img, (cx - img.get_width() // 2, cy - img.get_height() // 2))
        vida = int(enemigo.get("vida", 0))
        bx, by = cx - TAM // 2, cy - TAM // 2  # casilla del enemigo
        _barra(sup, bx, cy - img.get_height() // 2 - 10, TAM, 6, vida,
               max(ref_vida.get(enemigo.get("instancia", ""), vida), vida, 1))
        etiqueta = fuente.render(f"{i + 1}:{enemigo.get('instancia', '?')} {vida}",
                                  True, paleta.TEXTO)
        sup.blit(etiqueta, (cx - etiqueta.get_width() // 2,
                            cy + img.get_height() // 2 + 2))
        if enemigo.get("instancia") == golpe:
            pygame.draw.rect(sup, (255, 255, 255), pygame.Rect(bx - 2, by - 2, TAM + 4, TAM + 4), 3)
        if enemigo.get("instancia") in alcance:
            pygame.draw.rect(sup, (0, 220, 0), pygame.Rect(bx - 2, by - 2, TAM + 4, TAM + 4), 2)
        if i == sel_enemigo % max(len(vivos), 1):
            pygame.draw.rect(sup, paleta.TITULO, pygame.Rect(bx, by, TAM, TAM), 2)


def _barra(sup: pygame.Surface, x: int, y: int, w: int, h: int,
           vida: int, referencia: int) -> None:
    """Barra proporcional a la primera vida vista (guía §8; K5 no trae máximo)."""
    referencia = max(referencia, 1)
    pygame.draw.rect(sup, paleta.VIDA_FONDO, pygame.Rect(x, y, w, h))
    pygame.draw.rect(sup, paleta.VIDA,
                     pygame.Rect(x, y, max(0, w * min(vida, referencia) // referencia), h))
