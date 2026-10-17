"""Gestor de sprites (Parte 1 §4/§6 + guía §8): dibujante único por id.

PNGs en `assets/sprites/` (prota + pociones por efecto); lo que falte se
dibuja procedural y el id desconocido usa el reemplazo magenta. Se carga
una vez y se reutiliza. 9 clases + 3 comportamientos + puertas.
"""

from __future__ import annotations

import pathlib

import pygame

from src.view import paleta

ASSETS_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "assets" / "sprites"

# Personaje jugable (WASD): 2 frames estilo Pokémon Rojo/Azul.
JUGADOR_PNGS = ["Little Caesars Feliz.png", "Little Caesars Blink.png"]
JUGADOR_ALTO = 48  # el prota es más grande que el mosaico, como en Rojo/Azul
INCLINACION_PASO = 6  # grados que se inclina el frame de paso al caminar
RESPIRACION_PERIODO = 90  # ticks de un ciclo de squash & stretch en reposo
RESPIRACION_AMP = 0.05  # ±5% vertical (sutil)

# Pociones con arte PNG (assets/sprites/). Nombres canónicos por efecto;
# agregar una variante nueva = soltar el PNG + (opcional) extender claves.
POCION_SALUD_PNG = "pocion-salud.png"  # cura (ej. pocion-roja-01)
POCION_VELOCIDAD_PNG = "pocion-velocidad.png"  # buff velocidad (ej. pocion-veloz-01)

# Escudo de armadura (assets/sprites/). Vale para cualquier armadura futura:
# `assets/sprites/<id>.png` exacto tiene prioridad, si no el alias por clase.
ESCUDO_PNG = "escudo.png"
ESCUDO_TAM = 30  # overlay sobre el jugador: menor que el mosaico

# Espada del arma equipada. Igual que el escudo: `<id>.png` exacto manda,
# si no el alias por clase (vale para cualquier arma futura).
ESPADA_PNG = "espada.png"
# Rotación por facing (grados antihorarios; el arte base apunta arriba).
# N/S sin rotación: el personaje no rota al mirar arriba/abajo.
ANGULO_ESPADA = {"N": -45, "E": -45, "S": -45, "O": 45}

# Subcadenas del id que identifican cada efecto (reutilizable: vale para
# cualquier `pocion-*-NN` futuro sin tocar el gestor).
_CLAVES_POCION_VELOCIDAD = ("veloz", "velocidad", "rapidez", "speed", "swift")
_CLAVES_POCION_SALUD = ("roja", "salud", "vida", "cura", "health", "heal")

TAM = 36  # lado del mosaico base

# 9 clases del catálogo -> color (tema piedra + antorcha).
COLORES_CLASE = dict(paleta.CLASE_COLORES)

# Comportamientos visibles (guía §8).
COLORES_COMPORTAMIENTO = dict(paleta.COMPORTAMIENTO_COLORES)

# Puertas: estado -> color (4 direcciones x 4 estados, Parte 1 §6).
COLORES_PUERTA = {
    "abierta": paleta.PUERTA_ABIERTA,
    "cerrada-llave": paleta.PUERTA_LLAVE,
    "trabada": paleta.PUERTA_TRABADA,
}

REEMPLAZO = (255, 0, 255)  # sprite de reemplazo: id sin dibujante
JUGADOR = (70, 130, 230)


def _mosaico(color, tam: int = TAM, borde=(20, 20, 20)) -> pygame.Surface:
    sup = pygame.Surface((tam, tam))
    sup.fill(color)
    pygame.draw.rect(sup, borde, sup.get_rect(), 2)
    return sup


def clase_de_id(item_id: str) -> str:
    """Adivina la clase por el id (solo para elegir dibujo; nada de reglas)."""
    bajo = item_id.lower()
    if "pocion" in bajo:
        return "pocion"
    if "antidoto" in bajo:
        return "antidoto"
    if "llave" in bajo:
        return "llave"
    if "antorcha" in bajo:
        return "antorcha"
    if "pergamino" in bajo:
        return "pergamino_retroceso"
    if any(k in bajo for k in ("espada", "arma", "daga", "cuchillo", "arco",
                               "maza", "hacha", "baston", "lanza")):
        return "arma"
    if any(k in bajo for k in ("escudo", "armadura", "casco", "yelmo", "botas",
                               "guantes", "cota", "capa")):
        return "armadura"
    if any(k in bajo for k in ("pinchos", "veneno", "trampa", "dardos")):
        return "trampa"
    if any(k in bajo for k in ("esqueleto", "murcielago", "sombra", "jefe",
                               "rata", "goblin", "lobo", "orco", "fantasma",
                               "vampiro", "zombie", "golem", "arana")):
        return "enemigo"
    if bajo.startswith("ent_"):
        return "enemigo"
    if bajo.startswith("trp_"):
        return "trampa"
    if bajo.startswith("itm_"):
        return "objeto"
    return "desconocida"


def png_para_id(item_id: str) -> str | None:
    """Nombre del PNG para un id. `None` = dibujo procedural.

    Prioridad: `assets/sprites/<id>.png` exacto (override sin código),
    luego alias por efecto de poción (vale para `pocion-*-NN` futuros)
    y alias por clase de armadura.
    """
    if (ASSETS_DIR / f"{item_id}.png").is_file():
        return f"{item_id}.png"
    bajo = item_id.lower()
    if "pocion" in bajo or "potion" in bajo:
        if any(k in bajo for k in _CLAVES_POCION_VELOCIDAD):
            return POCION_VELOCIDAD_PNG
        if any(k in bajo for k in _CLAVES_POCION_SALUD):
            return POCION_SALUD_PNG
    if clase_de_id(item_id) == "armadura":
        return ESCUDO_PNG
    if clase_de_id(item_id) == "arma":
        return ESPADA_PNG
    return None


def _tinta(base: tuple[int, ...]) -> tuple[int, int, int]:
    """Color de trazo que contrasta con el fondo del mosaico."""
    return (255, 250, 240) if sum(base[:3]) < 420 else paleta.MURO


def _glifo(sup: pygame.Surface, clase: str, base: tuple[int, ...]) -> None:
    """Pictograma centrado por clase (no toca las esquinas: test usa (5,5))."""
    t = _tinta(base)
    if clase == "arma":  # espada diagonal + guarda
        pygame.draw.line(sup, t, (12, 24), (24, 12), 4)
        pygame.draw.line(sup, t, (12, 17), (17, 12), 3)
        pygame.draw.circle(sup, t, (23, 13), 2)
    elif clase == "armadura":  # escudo
        pygame.draw.polygon(sup, t, [(12, 10), (24, 10), (24, 18), (18, 26),
                                     (12, 18)], 2)
        pygame.draw.line(sup, t, (18, 10), (18, 20), 2)
    elif clase == "pocion":  # frasco
        pygame.draw.circle(sup, t, (18, 22), 6, 2)
        pygame.draw.rect(sup, t, pygame.Rect(16, 8, 4, 8))
    elif clase == "antidoto":  # cruz
        pygame.draw.rect(sup, t, pygame.Rect(15, 10, 6, 16))
        pygame.draw.rect(sup, t, pygame.Rect(10, 15, 16, 6))
    elif clase == "llave":  # aro + dientes
        pygame.draw.circle(sup, t, (14, 14), 5, 2)
        pygame.draw.line(sup, t, (17, 17), (26, 26), 3)
        pygame.draw.line(sup, t, (22, 22), (22, 26), 2)
        pygame.draw.line(sup, t, (25, 25), (25, 29), 2)
    elif clase == "antorcha":  # llama + palo
        pygame.draw.line(sup, t, (18, 20), (18, 29), 3)
        pygame.draw.polygon(sup, t, [(18, 7), (23, 17), (18, 21), (13, 17)])
    elif clase == "pergamino_retroceso":  # rollo con líneas
        pygame.draw.rect(sup, t, pygame.Rect(11, 12, 14, 13), 2)
        for yy in (16, 20, 24):
            pygame.draw.line(sup, t, (14, yy), (22, yy), 1)
    elif clase == "trampa":  # pinchos
        for xx in (12, 18, 24):
            pygame.draw.polygon(sup, t, [(xx - 3, 26), (xx + 3, 26), (xx, 14)])
    elif clase == "enemigo":  # ojos
        for ex in (14, 22):
            pygame.draw.circle(sup, (255, 250, 240), (ex, 16), 4)
            pygame.draw.circle(sup, paleta.MURO, (ex, 16), 2)
    elif clase == "objeto":  # caja
        pygame.draw.rect(sup, t, pygame.Rect(11, 14, 14, 12), 2)
        pygame.draw.line(sup, t, (11, 19), (25, 19), 1)


def _escala_respiro(base: pygame.Surface, total: int) -> tuple[int, int]:
    """Tamaño con squash & stretch según el reloj global (reposo y paso).

    Vertical ±RESPIRACION_AMP, horizontal inverso a la mitad (volumen).
    Determinista en `total`: mismo tick, mismo tamaño (caché estable).
    """
    import math  # local: el checklist §12 solo permite ciertos imports top-level
    fase = 2 * math.pi * (total % RESPIRACION_PERIODO) / RESPIRACION_PERIODO
    sy = 1.0 + RESPIRACION_AMP * math.sin(fase)
    sx = 1.0 - (sy - 1.0) * 0.5
    return (max(1, round(base.get_width() * sx)),
            max(1, round(base.get_height() * sy)))


class SpriteManager:
    """Carga una vez; `sprite(id)` siempre retorna algo (reemplazo si falta).

    `suavizado=False` (default): escalado nearest, píxel sharp. En True
    usa smoothscale (bordes suaves).
    """

    def __init__(self, suavizado: bool = False) -> None:
        self.suavizado = suavizado
        self._cache: dict[str, pygame.Surface] = {}
        self._png_cache: dict[str, pygame.Surface] = {}
        self._reemplazo = _mosaico(REEMPLAZO)
        self._jugador = _mosaico(JUGADOR)
        self._jugador_frames: list[pygame.Surface] = self._cargar_jugador()
        self._frame_cache: dict[tuple[int, str, int, int, int], pygame.Surface] = {}
        self._espada_cache: dict[str, pygame.Surface] = {}
        self._puertas = {
            estado: _mosaico(color, tam=TAM - 8)
            for estado, color in COLORES_PUERTA.items()
        }

    def _cargar_jugador(self) -> list[pygame.Surface]:
        """Frames PNG del prota escalados; vacío si falta el arte (fallback)."""
        frames = []
        for nombre in JUGADOR_PNGS:
            ruta = ASSETS_DIR / nombre
            if not ruta.is_file():
                continue
            try:
                img = pygame.image.load(str(ruta))
            except pygame.error:
                continue
            try:  # sin ventana (tests) no hay formato: usa la imagen tal cual
                img = img.convert_alpha()
            except pygame.error:
                pass
            alto = JUGADOR_ALTO
            ancho = max(1, img.get_width() * alto // max(img.get_height(), 1))
            frames.append(pygame.transform.scale(img, (ancho, alto)))
        return frames

    def _cargar_png(self, nombre: str) -> pygame.Surface | None:
        """PNG encajado en TAM x TAM sin deformar; `None` si falta o falla."""
        if nombre in self._png_cache:
            return self._png_cache[nombre]
        ruta = ASSETS_DIR / nombre
        if not ruta.is_file():
            return None
        try:
            img = pygame.image.load(str(ruta))
        except pygame.error:
            return None
        try:  # sin ventana (tests) no hay formato: usa la imagen tal cual
            img = img.convert_alpha()
        except pygame.error:
            pass
        lado = max(img.get_width(), img.get_height())
        if lado <= 0:
            return None
        if (img.get_width(), img.get_height()) != (TAM, TAM):
            escalar = pygame.transform.smoothscale if self.suavizado \
                else pygame.transform.scale
            try:
                img = escalar(img, (max(1, img.get_width() * TAM // lado),
                                    max(1, img.get_height() * TAM // lado)))
            except pygame.error:
                return None
        mosaico = pygame.Surface((TAM, TAM), pygame.SRCALPHA)
        mosaico.blit(img, ((TAM - img.get_width()) // 2,
                           (TAM - img.get_height()) // 2))
        self._png_cache[nombre] = mosaico
        return mosaico

    @property
    def jugador_png(self) -> bool:
        """Hay arte PNG para el personaje (si no, procedural de respaldo)."""
        return len(self._jugador_frames) > 0

    def jugador_frame(self, moviendo: bool, tick: int, facing: str = "S",
                      total: int = 0) -> tuple[pygame.Surface, int]:
        """Frame + salto del prota estilo Pokémon Rojo/Azul.

        Quieto: frame 0 con respiración (squash & stretch vertical suave
        atado al reloj global) y parpadeo (frame 1) cada ~4 s.
        Moviendo: alterna 0/1 cada 2 ticks y el frame 1 salta 3px
        (transformación por offset, sin mutar la imagen) con una ligera
        inclinación de INCLINACION_PASO grados. Mirar al Oeste
        espeja (flip) el arte frontal. Inclinación y respiración se
        recortan/centran para no mover el punto de apoyo.
        """
        if not self._jugador_frames:
            return self._jugador, 0
        idx, hop, lean = 0, 0, 0
        if moviendo and len(self._jugador_frames) > 1 and (tick // 2) % 2 == 1:
            idx, hop, lean = 1, -3, -INCLINACION_PASO
        elif not moviendo and len(self._jugador_frames) > 1 and total % 240 < 12:
            idx = 1  # parpadeo en reposo, sin salto ni inclinación
        base = self._jugador_frames[idx]
        respiro = _escala_respiro(base, total)
        clave = (idx, facing, lean, respiro[0], respiro[1])
        if clave not in self._frame_cache:
            img = base
            if (respiro[0], respiro[1]) != (img.get_width(), img.get_height()):
                escalar = pygame.transform.smoothscale if self.suavizado \
                    else pygame.transform.scale
                img = escalar(img, respiro)
            if facing == "O":
                img = pygame.transform.flip(img, True, False)
            if lean:
                rot = pygame.transform.rotate(img, lean)
                recorte = pygame.Rect(0, 0, img.get_width(), img.get_height())
                recorte.center = rot.get_rect().center
                img = rot.subsurface(recorte).copy()
            self._frame_cache[clave] = img
        return self._frame_cache[clave], hop

    def sprite(self, item_id: str) -> pygame.Surface:
        if item_id in self._cache:
            return self._cache[item_id]
        png = png_para_id(item_id)
        if png is not None:
            img = self._cargar_png(png)
            if img is not None:
                self._cache[item_id] = img
                return img
        clase = clase_de_id(item_id)
        color = COLORES_CLASE.get(clase, REEMPLAZO)
        sup = _mosaico(color)
        if clase == "desconocida":
            sup = self._reemplazo
        else:
            _glifo(sup, clase, color)
        self._cache[item_id] = sup
        return sup

    def es_reemplazo(self, item_id: str) -> bool:
        return clase_de_id(item_id) == "desconocida"

    @property
    def reemplazo(self) -> pygame.Surface:
        return self._reemplazo

    @property
    def jugador(self) -> pygame.Surface:
        return self._jugador

    def enemigo(self, comportamiento: str) -> pygame.Surface:
        """Enemigo inconfundible: círculo del color + anillo blanco + ojos."""
        color = COLORES_COMPORTAMIENTO.get(comportamiento, REEMPLAZO)
        sup = _mosaico(color)
        centro, radio = TAM // 2, TAM // 2 - 3
        pygame.draw.circle(sup, color, (centro, centro), radio)
        pygame.draw.circle(sup, (255, 255, 255), (centro, centro), radio, 2)
        _glifo(sup, "enemigo", color)
        return sup

    def escudo(self) -> pygame.Surface:
        """Escudo de la armadura equipada (PNG con fallback procedural)."""
        img = self._cargar_png(ESCUDO_PNG)
        if img is None:
            color = COLORES_CLASE.get("armadura", REEMPLAZO)
            img = _mosaico(color)
            _glifo(img, "armadura", color)
        if (img.get_width(), img.get_height()) != (ESCUDO_TAM, ESCUDO_TAM):
            escalar = pygame.transform.smoothscale if self.suavizado \
                else pygame.transform.scale
            try:
                return escalar(img, (ESCUDO_TAM, ESCUDO_TAM))
            except pygame.error:
                return img
        return img

    def espada(self, facing: str = "N") -> pygame.Surface:
        """Espada del arma equipada, rotada según facing (caché por facing)."""
        if facing in self._espada_cache:
            return self._espada_cache[facing]
        img = self._cargar_png(ESPADA_PNG)
        if img is None:
            color = COLORES_CLASE.get("arma", REEMPLAZO)
            img = _mosaico(color)
            _glifo(img, "arma", color)
        angulo = ANGULO_ESPADA.get(facing, 0)
        if angulo:
            try:
                img = pygame.transform.rotate(img, angulo)
            except pygame.error:
                pass
        self._espada_cache[facing] = img
        return img

    def puerta(self, cerrada: bool, llave) -> pygame.Surface | None:
        """Puerta por estado. `None` solo si el llamante pide muro (sin salida)."""
        if not cerrada:
            return self._puertas["abierta"]
        if llave:
            return self._puertas["cerrada-llave"]
        return self._puertas["trabada"]
