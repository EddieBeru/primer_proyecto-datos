"""Integración SDL del panel y política visual del reporte003."""

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from src.controller1.fake_provider import CRIPTA_ID, FakeProvider
from src.models.resolubilidad import UbicacionesLlaves
from src.orchestrator.sesion import Sesion
from src.orchestrator.reporte_resolubilidad import texto_reporte
from src.view import pantallas, texto, paleta
from src.view.tipografia import contraste
from src.view.app import VistaApp
from test_sesion import FakeBackend


def test_resultado_se_ve_antes_de_instalar_foto_y_contenido(monkeypatch):
    pygame.init()
    ses = Sesion(backend=FakeBackend(), log_ruta=None)
    app = VistaApp(ses, ventana=pygame.Surface((640, 480)))
    monkeypatch.setattr(app, "_pintar_carga", lambda *_: None)
    app.iniciar_partida(CRIPTA_ID)
    assert ses.estado is None and app.foto is None
    assert app.pantalla == "reporte_resolubilidad"
    assert app.reporte_resolubilidad == texto_reporte(ses.reporte_inicio())
    app.manejar_tecla(pygame.K_ESCAPE)
    assert app.pantalla == "seleccion" and ses.estado is None


def test_negativo_no_se_puede_continuar_sin_forzar(monkeypatch):
    pygame.init()
    backend = FakeBackend()
    backend.ubicaciones_llaves = lambda *args: UbicacionesLlaves(
        CRIPTA_ID, backend.fake._general.version, True, ())
    ses = Sesion(backend=backend, log_ruta=None)
    app = VistaApp(ses, ventana=pygame.Surface((640, 480)))
    monkeypatch.setattr(app, "_pintar_carga", lambda *_: None)
    app.iniciar_partida(CRIPTA_ID)
    assert ses.reporte_inicio().estado == "no_resoluble"
    app.manejar_tecla(pygame.K_1)
    assert ses.estado is None and app.pantalla == "reporte_resolubilidad"


def test_panel_mantiene_ids_largos_completos_y_desplazables():
    pygame.init()
    ventana = pygame.Surface((640, 480))
    reporte = "\n".join(f"Identificador-{i}-" + "x" * 120 for i in range(30))
    hotspots, limite = pantallas.pantalla_reporte_resolubilidad(
        ventana, pygame.font.Font(None, 20), reporte)
    assert len(hotspots) == 2 and limite > 0
    pantallas.pantalla_reporte_resolubilidad(
        ventana, pygame.font.Font(None, 20), reporte, scroll=limite)


def test_nombre_extenso_de_cripta_se_completa_con_foco_y_ratón():
    pygame.font.init()
    ventana = pygame.Surface((640, 480))
    nombre = "Catacumbas con nombre extenso para revisar ajuste"
    fuente = pygame.font.Font(None, 20)

    texto.iniciar_frame()
    hotspots = pantallas.pantalla_seleccion(
        ventana, fuente, [{"id": "larga", "nombre": nombre,
                          "salas": 300, "dificultad": 4}])
    texto.dibujar_ayuda(ventana, foco=hotspots[0][0])
    assert texto._AYUDA_TEXTO == "Catacumbas con nombre extenso para revisar ajuste"
    assert texto._AYUDA_RECT is not None
    assert ventana.get_rect().contains(texto._AYUDA_RECT)

    texto.iniciar_frame()
    hotspots = pantallas.pantalla_seleccion(
        ventana, fuente, [{"id": "larga", "nombre": nombre,
                          "salas": 300, "dificultad": 4}])
    pos = texto._AYUDAS[0][0].center
    texto.dibujar_ayuda(ventana, raton=pos)
    assert texto._AYUDA_TEXTO == nombre
    assert ventana.get_rect().contains(texto._AYUDA_RECT)


def test_tarjeta_compacta_separa_badge_del_nombre_y_datos(monkeypatch):
    pygame.font.init()
    ventana = pygame.Surface((640, 480))
    nombre = "Catacumbas con nombre extenso para revisar ajuste"
    cajas = {}
    insignias = []
    etiqueta_original = texto.etiqueta
    insignia_original = pantallas._insignia

    def registrar_etiqueta(sup, fuente, contenido, rect, color, **kwargs):
        if contenido in (nombre, "Salas: 300"):
            cajas[contenido] = rect.copy()
        return etiqueta_original(sup, fuente, contenido, rect, color, **kwargs)

    def registrar_insignia(*args, **kwargs):
        insignias.append((args[1], kwargs.get("lado", 36)))
        return insignia_original(*args, **kwargs)

    monkeypatch.setattr(texto, "etiqueta", registrar_etiqueta)
    monkeypatch.setattr(pantallas, "_insignia", registrar_insignia)
    pantallas.pantalla_seleccion(
        ventana, pygame.font.Font(None, 20),
        [{"id": "larga", "nombre": nombre, "salas": 300, "dificultad": 4}])

    badge_x, badge_y = insignias[-1][0]
    badge_lado = insignias[-1][1]
    badge_derecha = badge_x + badge_lado // 2
    assert cajas[nombre].left >= badge_derecha
    assert cajas["Salas: 300"].left >= badge_derecha
    assert cajas["Salas: 300"].right <= ventana.get_width()

def test_contraste_del_reporte_supera_minimo_de_texto_normal():
    assert contraste(paleta.TEXTO, paleta.PANEL) >= 4.5
    assert contraste(paleta.ACCION, paleta.PANEL) >= 4.5
    assert contraste(paleta.TEXTO_CLARO, paleta.ACCION) >= 4.5
