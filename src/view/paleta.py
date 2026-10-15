"""Paleta oficial de la vista (tema Little Caesars: naranja vivo + blanco).

Fondos crema brillantes, texto marrón oscuro, acento naranja intenso.
Peligro en rojo vivo, vida en verde, magia en morado.
El reemplazo sigue magenta y el jugador procedural azul (tests).
"""

from __future__ import annotations

# App / pantallas (claro y vivo).
FONDO_APP = (255, 244, 230)  # crema
PANEL = (255, 252, 245)  # blanco cálido para paneles
TITULO = (230, 92, 0)  # naranja intenso para títulos y selecciones
TEXTO = (62, 39, 26)  # marrón oscuro para texto sobre claro
TEXTO_CLARO = (255, 250, 240)  # para texto sobre rojo/naranja oscuro
SECUNDARIO = (140, 110, 85)  # marrón suave para texto secundario

# Sala (arena cálida + muros marrón).
FONDO_SALA = (246, 225, 190)
PISO_ALT = (238, 212, 172)  # damero del piso
MURO = (122, 72, 32)
ETIQUETA_FONDO = (255, 252, 245)  # respaldo de etiquetas del suelo

# HUD.
VIDA = (46, 160, 60)
VIDA_FONDO = (255, 205, 190)
PELIGRO = (215, 48, 31)
PELIGRO_FONDO = (120, 25, 15)
EQUIPADO = TITULO
MAGIA = (155, 126, 217)

# Puertas (misma semántica, tonos vivos).
PUERTA_ABIERTA = (46, 160, 60)
PUERTA_LLAVE = (215, 48, 31)
PUERTA_TRABADA = (150, 140, 130)
LLAVE_PUNTO = (230, 92, 0)

# Enemigos por comportamiento (distintos entre sí).
ENEMIGO_GUARDIAN = (215, 48, 31)
ENEMIGO_ERRANTE = (230, 130, 40)
ENEMIGO_RASTREADOR = (155, 126, 217)

# 9 clases del catálogo -> mosaico (+ genérico para itm_ sin clave).
CLASE_COLORES = {
    "enemigo": (215, 48, 31),
    "arma": (150, 160, 200),
    "armadura": (110, 130, 175),
    "pocion": (220, 80, 120),
    "antidoto": (90, 200, 120),
    "llave": (230, 150, 20),
    "antorcha": (240, 140, 40),
    "pergamino_retroceso": (155, 126, 217),
    "trampa": (130, 120, 110),
    "objeto": (170, 150, 120),
}

COMPORTAMIENTO_COLORES = {
    "guardián": ENEMIGO_GUARDIAN,
    "errante": ENEMIGO_ERRANTE,
    "rastreador": ENEMIGO_RASTREADOR,
}
