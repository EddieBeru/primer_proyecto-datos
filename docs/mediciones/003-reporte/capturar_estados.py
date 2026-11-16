"""Capturas headless de estados de interfaz para revisar 003."""

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tests"))

import pygame

from test_vista import FakeBackend
from src.controller1.fake_provider import CRIPTA_ID
from src.models.resolubilidad import ResultadoResolubilidad
from src.orchestrator.sesion import Sesion
from src.view.app import VistaApp
from src.view.historia import PanelHistoria


SALIDA = Path(__file__).resolve().parent
RESOLUCIONES = ((640, 480), (1024, 800), (1280, 720))
CRIPTAS = [
    {"id": "cripta-identificador-largo-0123456789",
     "nombre": "Catacumbas con nombre extenso para revisar ajuste",
     "salas": 300, "dificultad": 4},
    {"id": CRIPTA_ID, "nombre": "Cripta de prueba", "salas": 6,
     "dificultad": 1},
]


def capturar():
    pygame.init()
    for ancho, alto in RESOLUCIONES:
        sesion = Sesion(backend=FakeBackend(), log_ruta=None)
        ventana = pygame.Surface((ancho, alto))
        app = VistaApp(sesion, ventana=ventana)

        def guardar(nombre):
            app.dibujar()
            pygame.image.save(app.ventana, SALIDA / f"{nombre}-{ancho}x{alto}.png")

        app.preparar_menu(CRIPTAS, puede_continuar=True)
        guardar("menu")
        app.listar_para_seleccion(CRIPTAS, puede_continuar=True)
        guardar("seleccion")
        app.raton_pos = app.hotspots[0][0].center
        guardar("seleccion-nombre-completo")
        app.raton_pos = None

        identificador = "llave-identificador-extenso-0123456789-abcdef"
        contenido_largo = "\n".join((
            "Cripta: cripta-con-identificador-extenso-0123456789",
            "Resultado: NO RESOLUBLE",
            "Motivo: no se obtiene la llave de salida " + identificador,
            "Llaves no obtenibles:",
            *(f"{identificador}-{i:02d}" for i in range(18)),
            "Frontera bloqueada:",
            *(f"sala {i} / E -> sala {i + 1}; requiere {identificador}"
              for i in range(10)),
            "Ubicaciones:",
            *(f"{identificador}-{i:02d}: sala {i + 1}" for i in range(18)),
            "Ciclo bloqueante:",
            f"{identificador} -> llave-intermedia -> {identificador}",
        ))
        app.pantalla = "reporte_resolubilidad"
        app.reporte_resolubilidad = contenido_largo
        app.cripta_pendiente = (
            CRIPTA_ID, 0,
            ResultadoResolubilidad(CRIPTA_ID, "fake-v1", "no_resoluble"), False)
        guardar("reporte-error-largo")
        app.scroll_reporte = 520
        guardar("reporte-error-largo-scroll")

        app.iniciar_partida(CRIPTA_ID)
        app.manejar_tecla(pygame.K_1)
        guardar("hud")

        app.panel_mapa = True
        guardar("mapa")
        app.panel_mapa = False
        app.panel_historia = PanelHistoria(sesion)
        guardar("historial")
    pygame.quit()


if __name__ == "__main__":
    capturar()
