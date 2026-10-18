"""Texto de la vista: ajuste de línea y etiquetas con emoji.

Sin dependencias de juego: solo pygame (fuente) y stdlib.
Los emojis van por subcadena del id (API real + fake sin catálogo
exhaustivo) y solo como prefijo legible; el mosaico sigue dibujándose.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # solo tipos
    import pygame

# (subcadenas, emoji): primera coincidencia gana.
EMOJI_POR_CLAVE: tuple[tuple[tuple[str, ...], str], ...] = (
    (("llave",), "🔑"),
    (("pocion",), "🧪"),
    (("antidoto",), "💊"),
    (("antorcha",), "🔥"),
    (("pergamino",), "📜"),
    (("espada", "arma", "daga"), "🗡️"),
    (("escudo", "armadura"), "🛡️"),
    (("pinchos", "veneno", "trampa", "dardos"), "⚠️"),
    (("rata",), "🐀"),
    (("murcielago",), "🦇"),
    (("esqueleto",), "💀"),
    (("sombra",), "👤"),
    (("jefe", "goblin"), "👹"),
)

EMOJI_FALLBACK = "❔"

_PREFIJOS_ID = ("itm_", "ent_", "trp_")


def emoji_para(item_id: str) -> str:
    """Emoji por subcadena del id; ❔ si no hay coincidencia.

    Solo para terminal/consola (ahí sí se renderiza); Pygame usa
    pictogramas dibujados (ver `sprites._glifo`).
    """
    bajo = str(item_id).lower()
    for claves, emoji in EMOJI_POR_CLAVE:
        if any(k in bajo for k in claves):
            return emoji
    return EMOJI_FALLBACK


def nombre_corto(item_id: str) -> str:
    """Id legible: sin prefijo, sin sufijo -01, guiones a espacios."""
    nombre = str(item_id)
    for prefijo in _PREFIJOS_ID:
        if nombre.startswith(prefijo):
            nombre = nombre[len(prefijo):]
            break
    if "-" in nombre:
        base, _, sufijo = nombre.rpartition("-")
        if sufijo.isdigit():
            nombre = base
    return nombre.replace("-", " ").replace("_", " ").strip() or str(item_id)


def etiqueta_item(item_id: str) -> str:
    """Nombre corto para inventario y suelo (sin unicode: la fuente Pygame
    no trae glifos emoji; el pictograma va dibujado en el mosaico)."""
    return nombre_corto(item_id)


_DIRECCIONES = {"n": "norte", "s": "sur", "e": "este", "o": "oeste"}


def humanizar(linea: str) -> str:
    """Línea de bitácora `seq|tipo|actor|detalle` -> frase para el jugador.

    Solo presentación: nunca inventa datos; si el tipo no se reconoce,
    devuelve el detalle tal cual (o la línea original si ni eso).
    """
    partes = str(linea).split("|")
    if len(partes) < 4:
        return str(linea)
    _, tipo, actor, detalle = partes[0], partes[1], partes[2], partes[3]
    if tipo == "mover":
        if actor == "jugador":
            if detalle == "esperar":
                return "Esperaste un turno"
            return f"Te moviste al {_DIRECCIONES.get(detalle.lower(), detalle)}"
        return "Un enemigo se movió"
    if tipo == "abrir":
        return f"Abriste la puerta al {_DIRECCIONES.get(detalle.lower(), detalle)}"
    if tipo == "atacar":
        return f"Atacaste a {nombre_corto(detalle)}"
    if tipo == "dano":
        return f"Recibiste {detalle} de daño de {nombre_corto(actor)}"
    if tipo == "efecto":
        if actor == "trampa":
            return f"Se activó la trampa {nombre_corto(detalle)}"
        if actor == "oleada":
            return "Llegaron enemigos nuevos"
        if detalle.startswith(("pocion:", "antidoto:", "antorcha:")):
            clase, _, objeto = detalle.partition(":")
            return f"Usaste {clase} {nombre_corto(objeto)}"
        return f"Efecto: {detalle}"
    if tipo == "equipar":
        return f"Equipaste {nombre_corto(detalle)}"
    if tipo == "recoger":
        return f"Recogiste {nombre_corto(detalle)}"
    if tipo == "soltar":
        return f"Soltaste {nombre_corto(detalle)}"
    if tipo == "deshacer":
        return "Rebobinaste con un pergamino"
    if tipo == "muerte":
        return "Moriste" if detalle == "jugador" else f"Derrotaste a {nombre_corto(actor)}"
    return detalle or str(linea)


def envolver(texto: str, fuente: "pygame.Font", ancho_max: int,
             max_lineas: int = 5) -> list[str]:
    """Parte el texto en líneas que quepan en ancho_max píxeles.

    Corte por palabras; palabra más ancha que el límite se parte.
    Pasado max_lineas, la última termina en ….
    """
    if max_lineas <= 0:
        return []
    palabras: list[str] = []
    for bloque in str(texto).split(" "):
        while bloque and fuente.size(bloque)[0] > ancho_max:
            corte = len(bloque)
            while corte > 1 and fuente.size(bloque[:corte])[0] > ancho_max:
                corte -= 1
            palabras.append(bloque[:corte])
            bloque = bloque[corte:]
        if bloque:
            palabras.append(bloque)
    if not palabras:
        return [""]
    lineas = [" ".join(palabras)]
    if len(lineas) == 1 and fuente.size(lineas[0])[0] <= ancho_max:
        return lineas[:max_lineas]
    lineas = []
    actual = ""
    for palabra in palabras:
        prueba = f"{actual} {palabra}".strip()
        if fuente.size(prueba)[0] <= ancho_max or not actual:
            actual = prueba
        else:
            lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    if len(lineas) > max_lineas:
        lineas = lineas[:max_lineas]
        while lineas and fuente.size(lineas[-1] + "…")[0] > ancho_max:
            lineas[-1] = lineas[-1][:-1]
        lineas[-1] = (lineas[-1] + "…") if lineas else "…"
    return lineas
