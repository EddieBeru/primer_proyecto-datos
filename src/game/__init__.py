"""Capa de aplicación: orquestación de partida (el "tercer controlador").

C1 trae datos, C2 decide reglas, la Fachada traduce. Nadie coordinaba el
ciclo de vida: elegir cripta → semilla → esqueleto → sala inicial → loop
§2.3 (intención → drenar agenda → foto) → pausa/guardar/cargar → fin →
tabla + reporte. Eso vive aquí, delgado, sin reglas ni I/O directo.
"""

from src.game.sesion import ProveedorSesion, Sesion

__all__ = ["ProveedorSesion", "Sesion"]
