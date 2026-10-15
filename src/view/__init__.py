"""Vista Pygame (Parte 1 + guía de vista): solo habla con Sesión.

Regla de oro (§12): importar `src.orchestrator.sesion` (+ `OfflineBackend`
para probar). Nada de C1/C2, `RoomLoader`, `savegame` ni `EstadoPartida` en
este paquete (verificado en `tests/test_vista.py`).
"""

from src.view.app import AYUDA, FPS, VistaApp, rutas_log_por_defecto
from src.view.capas import dibujar_actores, dibujar_estatica, dibujar_fondo
from src.view.entrada import intencion_para_tecla, mover_para_tecla
from src.view.pantallas import (menu_pausa, pantalla_carga, pantalla_error,
                                pantalla_fin, pantalla_inicio,
                                pantalla_juego, pantalla_seleccion,
                                pantalla_version)
from src.view.sprites import SpriteManager, clase_de_id
from src.view.ui import (dibujar_barra_vida, dibujar_inventario,
                         dibujar_mensajes, dibujar_stats, dibujar_toast)

__all__ = [
    "AYUDA", "FPS", "SpriteManager", "VistaApp",
    "clase_de_id", "dibujar_actores", "dibujar_barra_vida",
    "dibujar_estatica", "dibujar_fondo", "dibujar_inventario",
    "dibujar_mensajes", "dibujar_stats", "dibujar_toast",
    "intencion_para_tecla", "menu_pausa", "mover_para_tecla",
    "pantalla_carga", "pantalla_error", "pantalla_fin", "pantalla_inicio",
    "pantalla_juego", "pantalla_seleccion", "pantalla_version",
    "rutas_log_por_defecto",
]
