"""Vista Pygame: checklist §12, teclado, sprites, pantallas y ruta completa.

Sin red ni presupuesto: todo corre contra FakeBackend local (6 salas).
Headless con SDL dummy. La ÚNICA prueba que toca el API real (y gasta
presupuesto) es `test_api_real`, salteada salvo `CRIPTA_API_REAL=1`.
"""

import ast
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pathlib

import pygame
import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- backend falso
from src.controller1.fake_provider import CRIPTA_ID, FakeProvider
from src.controller2.fachada import FotoEstado
from src.controller2.victoria import actualizar_estado
from src.models.catalog import CatalogVersion
from src.models.dungeons import DungeonVersion
from src.models.roomContents import ContenidoResponse
from src.orchestrator.sesion import Sesion


class FakeBackend:
    def __init__(self):
        self.fake = FakeProvider()

    def listar_criptas(self, budget=None):
        return self.fake.listar_criptas()

    def info_cripta(self, cripta_id, budget=None):
        return self.fake.preparar_cripta(cripta_id)

    def version_cripta(self, cripta_id, budget=None):
        return DungeonVersion(id=cripta_id, version=self.fake._general.version)

    def version_catalogo(self, budget=None):
        return CatalogVersion(version="fake-cat-v1")

    def esqueleto_completo(self, cripta_id, budget=None, info=None):
        return dict(self.fake._salas)

    def contenido(self, cripta_id, salas, budget=None):
        return ContenidoResponse(
            contenido=[self.fake._contenido[s] for s in salas])

    def lote_catalogo_auto(self, ids, budget=None):
        return {i: self.fake.ficha(i) for i in dict.fromkeys(ids)}


@pytest.fixture()
def app(tmp_path):
    pygame.init()
    pantalla = pygame.Surface((960, 640))
    ses = Sesion(backend=FakeBackend(), log_ruta=None,
                 puntajes_ruta=str(tmp_path / "puntajes.jsonl"))
    from src.view.app import VistaApp
    vista = VistaApp(ses, ventana=pantalla,
                     save_path=str(tmp_path / "partida.bin"))
    vista.iniciar_partida(CRIPTA_ID)
    return vista


RUTA_VICTORIA = ["s", "recoger llave-hierro-01", "e", "abrir N", "n",
                 "abrir S", "s", "s", "o", "recoger llave-salida-01",
                 "abrir E", "e"]


# ------------------------------------------------------- §12 checklist imports
def test_solo_habla_con_sesion():
    permitidos = {"pygame", "src.view", "src.orchestrator.sesion",
                  "__future__", "dataclasses", "os", "pathlib", "typing"}
    for ruta in sorted((REPO / "src" / "view").glob("*.py")):
        arbol = ast.parse(ruta.read_text(encoding="utf-8"))
        for nodo in arbol.body:
            if isinstance(nodo, ast.If):  # TYPE_CHECKING no corre en runtime
                continue
            mods = []
            if isinstance(nodo, ast.Import):
                mods = [a.name for a in nodo.names]
            elif isinstance(nodo, ast.ImportFrom) and nodo.module:
                mods = [nodo.module]
            for mod in mods:
                assert any(mod == p or mod.startswith(p + ".") for p in permitidos), \
                    (ruta.name, mod)


# ------------------------------------------------------- teclado -> intenciones
def test_mapa_movimiento(app):
    from src.view.entrada import mover_para_tecla
    assert mover_para_tecla(pygame.K_w) == "n"
    assert mover_para_tecla(pygame.K_UP) == "n"
    assert mover_para_tecla(pygame.K_s) == "s"
    assert mover_para_tecla(pygame.K_a) == "o"
    assert mover_para_tecla(pygame.K_d) == "e"
    assert mover_para_tecla(pygame.K_F5) is None


def test_mapa_acciones(app):
    from src.view.entrada import intencion_para_tecla
    foto = app.foto
    assert intencion_para_tecla(pygame.K_e, foto, "N") == "abrir N"
    # Espacio/F/1-8 los resuelve el App por proximidad (no son intenciones fijas)
    assert intencion_para_tecla(pygame.K_SPACE, foto, "N") is None
    assert intencion_para_tecla(pygame.K_f, foto, "N") is None
    assert intencion_para_tecla(pygame.K_1, foto, "N") is None
    assert intencion_para_tecla(pygame.K_u, foto, "N") == "deshacer"
    assert intencion_para_tecla(pygame.K_TAB, foto, "N") == "@tab-inv"
    assert intencion_para_tecla(pygame.K_t, foto, "N") == "@tab-suelo"
    assert intencion_para_tecla(pygame.K_F1, foto, "N") == "@dev"
    assert intencion_para_tecla(pygame.K_g, foto, "N") == "@guardar"
    assert intencion_para_tecla(pygame.K_ESCAPE, foto, "N") == "@pausa"
    assert intencion_para_tecla(pygame.K_F5, foto, "N") is None
    # Bloque §4.5/objetivo: X fija objetivo, C cicla el orden de la mochila.
    assert intencion_para_tecla(pygame.K_x, foto, "N") == "@sel-enemigo"
    assert intencion_para_tecla(pygame.K_c, foto, "N") == "@criterio-inv"
    assert intencion_para_tecla(pygame.K_x, foto, "N",
                                mods=pygame.KMOD_SHIFT) == "@sel-enemigo-prev"
    assert intencion_para_tecla(pygame.K_TAB, foto, "N",
                                mods=pygame.KMOD_SHIFT) == "@tab-inv-prev"


def test_objetivo_con_x_y_space_ataca_al_fijado(app):
    assert app.manejar_tecla(pygame.K_x) == "@sel-enemigo"
    assert app.sel_enemigo_activo
    assert app.manejar_tecla(pygame.K_SPACE) == "atacar e1-1"


def test_cicla_criterio_de_mochila(app):
    assert app.manejar_tecla(pygame.K_c) == "@criterio-inv"
    assert app.criterio_inv == "nombre"
    assert app.manejar_tecla(pygame.K_c) == "@criterio-inv"
    assert app.criterio_inv == "peso"
    assert app._accion_local("@criterio-inv-prev") == "@criterio-inv-prev"
    assert app.criterio_inv == "nombre"
    assert app._accion_local("@criterio-inv-prev") == "@criterio-inv-prev"
    assert app.criterio_inv is None  # vuelve al orden real


def test_manejar_tecla_mueve_libre_sin_cambiar_sala(app):
    pos0 = list(app.pos_jugador)
    assert app.manejar_tecla(pygame.K_e) is None  # abrir N falla (no hay puerta)
    assert app.manejar_tecla(pygame.K_s) == "@paso"
    assert app.foto.sala_id == 1 and app.facing == "S"  # camina, no cruza
    assert app.pos_jugador[1] > pos0[1]


def test_movimiento_diagonal_normalizado(app):
    """Diagonal = recto: el vector se normaliza (no √2 más rápido)."""
    from src.view import app as mod
    app.pos_jugador = [0.5, 0.5]
    app._mover_libre(1, 1)
    dx = app.pos_jugador[0] - 0.5
    dy = app.pos_jugador[1] - 0.5
    assert abs((dx * dx + dy * dy) ** 0.5 - mod.VELOCIDAD) < 1e-9
    app.pos_jugador = [0.5, 0.5]
    app._mover_libre(1, 0)
    assert abs(app.pos_jugador[0] - 0.5 - mod.VELOCIDAD) < 1e-9
    assert app.pos_jugador[1] == 0.5
    app.pos_jugador = [0.5, 0.5]
    app._mover_libre(0, 0)  # teclas opuestas se cancelan: no mueve
    assert app.pos_jugador == [0.5, 0.5]


# ------------------------------------------------------- sprites y reemplazo
def test_sprites_cache_y_reemplazo():
    from src.view.sprites import SpriteManager
    pygame.init()
    sp = SpriteManager()
    assert sp.sprite("espada-hierro-01") is sp.sprite("espada-hierro-01")
    assert not sp.es_reemplazo("espada-hierro-01")
    raro = sp.sprite("cosa-del-profe-99")
    assert sp.es_reemplazo("cosa-del-profe-99")
    assert raro.get_at((5, 5))[:3] == (255, 0, 255)
    assert raro is sp.reemplazo
    # Todos los enemigos comparten el mismo sprite (solo cambia la IA).
    assert sp.enemigo("guardián").get_at((5, 5)) == \
        sp.enemigo("errante").get_at((5, 5)) == \
        sp.enemigo("rastreador").get_at((5, 5))
    assert sp.puerta(False, None).get_at((5, 5)) != \
        sp.puerta(True, "llave-hierro-01").get_at((5, 5))
    assert sp.puerta(True, None).get_at((5, 5)) != \
        sp.puerta(True, "llave-hierro-01").get_at((5, 5))


# ------------------------------------------------------- pantallas sin crashear
def test_grupos_de_items_comparten_arte(app):
    """Grupos similares reutilizan PNG: protección → escudo, armas → espada."""
    from src.view.sprites import clase_de_id, png_para_id
    assert clase_de_id("coraza-runica-01") == "armadura"
    assert png_para_id("coraza-runica-01") == "escudo.png"
    assert png_para_id("escudo-madera-01") == "escudo.png"
    assert png_para_id("mandoble-01") == "espada.png"
    # Frasco único: toda poción (también la veloz) y las curas (antídoto).
    assert png_para_id("antidoto-01") == "pocion-salud.png"
    assert png_para_id("pocion-roja-01") == "pocion-salud.png"
    assert png_para_id("pocion-veloz-01") == "pocion-salud.png"
    assert png_para_id("elixir-vital-futuro-02") == "pocion-salud.png"
    assert clase_de_id("llamas-01") == "trampa"
    assert png_para_id("llamas-01") == "trampa.png"
    assert clase_de_id("cosa-del-profe-99") == "desconocida"


def test_pantallas(app):
    from src.view import pantallas
    sup, fuente = app.ventana, app.fuente
    pantallas.pantalla_inicio(sup, fuente, False)
    pantallas.pantalla_inicio(sup, fuente, True, app.sprites)
    largo = [
        {"id": "a", "nombre": "A", "salas": 6, "dificultad": 1},
        {"id": "b", "nombre": "B", "salas": 3, "dificultad": 2},
        {"id": "c", "nombre": "El Horno Maldito de la Muerte Eterna",
         "salas": 9, "dificultad": 5},
        {"id": "d", "nombre": "D", "salas": 5, "dificultad": 3},
        {"id": "e", "nombre": "E", "salas": 7, "dificultad": 4}]
    pantallas.pantalla_seleccion(sup, fuente, largo[:2], app.sprites)
    pantallas.pantalla_seleccion(sup, fuente, largo, app.sprites)  # 3 col + envolver
    pantallas.pantalla_carga(sup, fuente)
    pantallas.pantalla_carga(sup, fuente, "El servidor pide esperar 5 segundos…")
    pantallas.pantalla_juego(sup, fuente, app.foto, app.sprites, app.area_sala())
    pantallas.pantalla_juego(sup, fuente, app.foto, app.sprites, app.area_sala(),
                             dev=True)
    pantallas.menu_pausa(sup, fuente)
    pantallas.pantalla_error(sup, fuente, "Sin conexión.")
    pantallas.pantalla_version(sup, fuente, "Versión anterior.")
    assert isinstance(app.foto, FotoEstado)


def test_dibujar_en_todas_las_pantallas(app):
    """App.dibujar con sprites reales no puede romper en ningún estado."""
    for comando in RUTA_VICTORIA:
        ok, msg, _ = app.enviar(comando)
        assert ok, (comando, msg)
    assert app.foto.estado == "victoria"
    for pantalla in ("fin", "inicio", "seleccion", "carga", "pausa", "juego",
                     "error", "version"):
        app.pantalla = pantalla
        app.dibujar()


def test_humanizar_bitacora():
    from src.view import texto as texto_vista
    assert texto_vista.humanizar("3|mover|jugador|s") == "Te moviste al sur"
    assert texto_vista.humanizar("4|mover|jugador|esperar") == "Esperaste un turno"
    assert texto_vista.humanizar("5|abrir|jugador|e") == "Abriste la puerta al este"
    assert texto_vista.humanizar("6|efecto|trampa|t3-1") == "Se activó la trampa t3"
    assert "Recibiste 4 de daño" in texto_vista.humanizar("7|dano|e1-1|4")
    assert texto_vista.humanizar("sin formato") == "sin formato"
    assert texto_vista.humanizar("8|raro|actor|detalle") == "detalle"


def test_caja_encajada_sin_cortes_y_area_dentro(app):
    """Arte contain (nada cortado), área jugable dentro y HUD sin tapar."""
    from src.view import capas
    from src.view.sprites import (CAJA_ARTE_ALTO, CAJA_ARTE_ANCHO,
                                  escala_caja)
    area = app.area_sala()
    rect = capas.rect_caja(area)
    assert rect.contains(area)
    escala = escala_caja(rect)
    assert CAJA_ARTE_ANCHO * escala <= rect.w + 1
    assert CAJA_ARTE_ALTO * escala <= rect.h + 1
    assert rect.bottom + 2 < app.ventana.get_height() - 120  # banda HUD libre


def test_zona_caja_cuadrada_y_rect_inverso(app):
    """El campo de juego es el hueco 110/290 del sprite (cuadrado), y
    `capas.rect_caja` reconstruye el rect del arte sin desviarse."""
    from src.view import capas
    from src.view.sprites import zona_caja
    area = app.area_sala()
    assert area.w == area.h  # hueco cuadrado, centrado en el sprite
    vuelta = zona_caja(capas.rect_caja(area))
    assert abs(vuelta.x - area.x) <= 2
    assert abs(vuelta.y - area.y) <= 2
    assert abs(vuelta.w - area.w) <= 2


def test_zoom_de_menu_a_partida(app, tmp_path):
    """Empezar partida desde el menú: zoom de la caja hasta la del juego."""
    from src.view.app import VistaApp, ZOOM_FRAMES
    ses = Sesion(backend=FakeBackend(), log_ruta=None,
                 puntajes_ruta=str(tmp_path / "puntajes.jsonl"))
    vista = VistaApp(ses, ventana=pygame.Surface((960, 640)),
                     save_path=str(tmp_path / "partida.bin"))
    vista.preparar_menu([{"id": CRIPTA_ID, "nombre": "A", "salas": 6,
                          "dificultad": 1}], False)
    vista.manejar_tecla(pygame.K_1)  # menú -> selección
    assert vista.manejar_tecla(pygame.K_1) == "@jugar"
    assert vista.pantalla == "juego" and vista.zoom_ttl == 0
    for _ in range(ZOOM_FRAMES):
        vista.dibujar()
    assert vista.zoom_ttl is None


def test_caja_pizza_abre_por_stages(app):
    """Menú: la tapa avanza 1 -> 6 con la cuenta de frames (y para en 6)."""
    from src.view import pantallas
    pantallas.pantalla_inicio(app.ventana, app.fuente, False, app.sprites,
                              apertura=0)
    assert pantallas.stage_caja(None) == 6
    assert pantallas.stage_caja(0) == 1
    assert pantallas.stage_caja(34) == 2
    assert pantallas.stage_caja(64) == 5
    assert pantallas.stage_caja(200) == 6


def test_caja_fondo_cubre_area_y_assets(app):
    """Box.png cubre el canvas exacto; los lids existen y no rompen."""
    fondo = app.sprites.caja_fondo(240, 180)
    assert fondo is not None and fondo.get_size() == (240, 180)
    assert app.sprites.caja(1) is not None
    assert app.sprites.caja(6) is not None


def test_menu_animacion_se_reinicia(app):
    """Entrar al menú reinicia la apertura; dibujar avanza la cuenta."""
    app._abrir_menu()
    app.dibujar()
    app.dibujar()
    assert app.menu_ttl == 2
    app._abrir_menu()
    assert app.menu_ttl == 0


def test_jugador_grande_nativo_y_cacheado(app):
    """Menús: el prota sale del PNG nativo (nítido), no del frame TAM."""
    sp = app.sprites
    chico = sp.jugador_frame(False, 0, "S", 0)[0]
    grande = sp.jugador_grande(2.0)
    assert grande.get_width() > chico.get_width() * 3
    assert grande.get_height() > chico.get_height() * 3
    assert grande is sp.jugador_grande(2.0)  # cache por (escala, espejo)
    espejado = sp.jugador_grande(2.0, espejo=True)
    assert espejado.get_size() == grande.get_size()


def test_arranque_abre_en_el_menu_principal(app):
    """Arranque normal: siempre menú; "1 Jugar" lleva a la selección.

    Antes, con una sola cripta el main saltaba directo a la partida y el
    menú nunca se veía.
    """
    from src.view.app import VistaApp
    vista = VistaApp(app.ses, ventana=pygame.Surface((960, 640)))
    vista.preparar_menu([{"id": "a", "nombre": "A", "salas": 6, "dificultad": 1}],
                        False)
    assert vista.pantalla == "inicio"
    vista.dibujar()  # pinta el menú principal sin crashear
    assert vista.manejar_tecla(pygame.K_1) == "@jugar"
    assert vista.pantalla == "seleccion"
    vista.dibujar()


def test_embestida_enemiga_marca_al_agresor(app):
    """Turno enemigo en la misma sala: la vista marca la embestida del atacante.

    e1-1 es el guardián de la sala 1 (vel 5): tras dos esperas su turno cae
    y ataca; el motor anota `dano|e1-1|N` y la vista lo detecta.
    """
    assert all("activa" in e for e in app.foto.enemigos)
    for _ in range(6):
        ok, msg, _ = app.enviar("esperar")
        assert ok, msg
        if app.golpes:
            break
    assert app.golpes, app.foto.mensajes[-3:]
    assert next(iter(app.golpes)) == "e1-1"
    assert 0 < app._fases_golpes()["e1-1"] <= 1
    app.dibujar()  # pinta la embestida sin crashear


def test_fin_teclas_jugar_de_nuevo_y_menu(app):
    for comando in RUTA_VICTORIA:
        ok, msg, _ = app.enviar(comando)
        assert ok, (comando, msg)
    app.dibujar()  # estado fin: fuerza finalizar() y pinta el resumen
    assert app.pantalla == "fin" and app.reporte is not None
    assert app.manejar_tecla(pygame.K_2) == "@menu"
    assert app.pantalla == "inicio"
    app.pantalla = "fin"
    app.dibujar()
    assert app.manejar_tecla(pygame.K_1) == "@jugar"
    assert app.pantalla == "juego" and app.cripta_actual == CRIPTA_ID
    assert app.foto.estado == "jugando" and app.reporte is None


def test_pantalla_fin_victoria_y_derrota(app):
    from src.view import pantallas
    for cmd in RUTA_VICTORIA:
        ok, msg, _ = app.enviar(cmd)
        assert ok, (cmd, msg)
    assert app.foto.estado == "victoria" and app.pantalla == "fin"
    reporte = app.finalizar()
    assert reporte["terminada"] is True
    pantallas.pantalla_fin(app.ventana, app.fuente, app.foto, reporte, app.sprites)
    app2_foto = app.foto
    app.ses.estado.jugador.vida_actual = 0
    actualizar_estado(app.ses.estado)
    assert app.ses.estado.estado == "derrota"
    foto_derrota = app.ses.fachada.foto()
    pantallas.pantalla_fin(app.ventana, app.fuente, foto_derrota, None)
    assert app2_foto.estado == "victoria"


# ------------------------------------------------------- ruta completa (§11)
def test_ruta_victoria_por_vista(app):
    for cmd in RUTA_VICTORIA:
        ok, msg, _ = app.enviar(cmd)
        assert ok, (cmd, msg)
        app.dibujar()
    assert app.foto.estado == "victoria"
    assert app.finalizar()["terminada"] is True


def test_error_amable_no_cambia_estado(app):
    sala, vida = app.foto.sala_id, app.foto.jugador["vida"]
    ok, msg, foto = app.enviar("volar")
    assert not ok and foto.error is not None
    assert foto.sala_id == sala and foto.jugador["vida"] == vida
    assert app.manejar_tecla(pygame.K_F5) is None
    app.dibujar()


def test_pausa_guardar_cargar(app):
    assert app.manejar_tecla(pygame.K_ESCAPE) == "@pausa"
    assert app.pantalla == "pausa"
    app.dibujar()
    assert app.manejar_tecla(pygame.K_g) == "@guardar"
    import os
    assert os.path.isfile(app.save_path)
    app.manejar_tecla(pygame.K_ESCAPE)
    assert app.pantalla == "juego"
    app.enviar("e")
    assert app.foto.sala_id == 2
    app.cargar_partida()
    assert app.foto.sala_id == 1


def test_deshacer_y_pergaminos(app):
    assert isinstance(app.foto.pergaminos, int) and app.foto.pergaminos == 0
    app.enviar("e")  # llena la pila para que el fallo sea por pergamino
    ok, msg, _ = app.enviar("deshacer")
    assert not ok and "pergamino" in msg.lower()
    assert app.manejar_tecla(pygame.K_TAB) == "@tab-inv"
    assert app.manejar_tecla(pygame.K_u) is None  # rechazado sin crash


# ------------------------------------------------------- rebobina del pergamino
def test_rebobina_anillos_violeta_y_apagado():
    from src.view import capas
    area = pygame.Rect(60, 60, 200, 180)
    caja = capas.rect_caja(area)
    sup = pygame.Surface((480, 480), pygame.SRCALPHA)
    puntos = [(x, y) for x in range(0, 480, 24) for y in range(0, 480, 24)
              if caja.collidepoint(x, y)]
    assert puntos
    capas.dibujar_rebobina(sup, area, 1.0)
    pintados = [p for p in puntos if sup.get_at(p)[3] > 0]
    assert pintados  # el destello cubre la sala...
    morados = [p for p in pintados if sup.get_at(p)[2] > sup.get_at(p)[0]]
    assert morados  # ... en tonos violeta (magia)
    # Apagado (fase 0) no pinta nada.
    apagado = pygame.Surface((480, 480), pygame.SRCALPHA)
    capas.dibujar_rebobina(apagado, area, 0.0)
    assert all(apagado.get_at(p)[3] == 0 for p in puntos)
    # Determinista: misma fase -> mismos píxeles (nada de azar en la vista).
    otra = pygame.Surface((480, 480), pygame.SRCALPHA)
    capas.dibujar_rebobina(otra, area, 1.0)
    assert all(otra.get_at(p) == sup.get_at(p) for p in puntos)


def test_deshacer_rebobina_y_reaparece_en_la_puerta(app):
    from src.view.app import REBOBINA_FRAMES
    app.ses.estado.jugador.inventario.append("pergamino-01")
    ok, _, _ = app.enviar("s")  # 1 -> 3
    assert ok and app.foto.sala_id == 3
    assert app.rebobina_ttl == 0
    ok, _, _ = app.enviar("deshacer")
    assert ok and app.foto.sala_id == 1
    assert app.rebobina_ttl == REBOBINA_FRAMES  # arranca el destello
    assert app.pos_jugador == [0.5, 0.9]  # del lado de la puerta S (la de 3)
    assert app.en_puerta  # no recruza al instante por proximidad
    for _ in range(REBOBINA_FRAMES):
        app.dibujar()
    assert app.rebobina_ttl == 0  # el destello expira solo
    # Deshacer dentro de la misma sala conserva la posición del prota.
    app.ses.estado.jugador.inventario.append("pergamino-01")
    ok, _, _ = app.enviar("esperar")
    assert ok
    antes = list(app.pos_jugador)
    ok, _, _ = app.enviar("deshacer")
    assert ok and app.foto.sala_id == 1 and app.rebobina_ttl == REBOBINA_FRAMES
    assert app.pos_jugador == antes
    # Un retroceso rechazado (sin pergaminos) no dispara el destello.
    assert app.foto.pergaminos == 0
    app.rebobina_ttl = 0  # ya consumido el del retroceso anterior
    ok, msg, _ = app.enviar("deshacer")
    assert not ok and app.rebobina_ttl == 0


# ------------------------------------------------------- CLI --vista (C1-10)
def test_cli_vista():
    from src.controller1.cli import parse_args
    assert parse_args([]).vista is False
    assert parse_args(["--vista"]).vista is True


# ------------------------------------------------------- sfx (guiño al empezar)
def test_jingle_al_empezar_partida(app, monkeypatch):
    llamadas = []
    monkeypatch.setattr(app.sfx, "jingle_inicio",
                        lambda: llamadas.append("jingle") or True)
    app.iniciar_partida(CRIPTA_ID)
    assert llamadas == ["jingle"]
    app.guardar()
    app.cargar_partida()  # retomar también es empezar a jugar
    assert len(llamadas) == 2


def test_jingle_sin_audio_no_rompe():
    from src.view.sfx import Sonidos
    pygame.init()
    assert isinstance(Sonidos().jingle_inicio(), bool)  # suene o no, no crashea


# ------------------------------------------------------- API real (presupuesto)
@pytest.mark.skipif(os.environ.get("CRIPTA_API_REAL") != "1",
                    reason="gasta presupuesto real; solo cuando todo esté funcional")
def test_api_real_listar_iniciar_un_paso():
    """ÚNICA prueba contra el API real: lista, inicia y da un paso por vista."""
    pygame.init()
    from src.view.app import VistaApp
    ses = Sesion(backend=None, jugador="vista-test", log_ruta=None)
    criptas = ses.backend.listar_criptas()
    assert criptas.criptas, "el API no devolvió criptas"
    primera = criptas.criptas[0].id
    foto = ses.iniciar(primera, semilla=0)
    assert foto.sala_id == ses.info.sala_inicial
    assert ses.budget.reporte()["realizadas"] > 0  # hubo red de verdad
    app = VistaApp(ses, ventana=pygame.Surface((960, 640)))
    app.foto = foto
    app.dibujar()


# ------------------------------------------------------- personaje que se mueve
def test_espejo_se_conserva_al_mirar_arriba_o_abajo(app):
    app._mover_libre(-1, 0)  # camina a la izquierda
    assert app.facing == "O" and app.espejo
    app._mover_libre(0, -1)  # luego arriba: NO voltea a la derecha
    assert app.facing == "N" and app.espejo
    app._mover_libre(0, 1)   # luego abajo: sigue mirando a la izquierda
    assert app.facing == "S" and app.espejo
    app._mover_libre(1, 0)   # al caminar a la derecha sí voltea
    assert app.facing == "E" and not app.espejo


def test_sin_brinco_al_cambiar_de_eje(app):
    for _ in range(6):
        app._mover_libre(1, 0)
        app.dibujar()
    assert app.paso_push[0] > 1  # venía empujando a la derecha
    app._mover_libre(0, -1)      # cambia a subir
    app.dibujar()
    assert app.paso_push[0] > 0  # el desplazamiento no salta de eje en 1 frame
    assert app.paso_push[1] < 0  # y ya empieza a subir suavemente


def test_espada_y_escudo_en_cache_por_lado():
    from src.view.sprites import SpriteManager
    pygame.init()
    sp = SpriteManager()
    izq = sp.espada("N", espejo=True)
    assert izq is sp.espada("O")  # el lado manda, no el facing
    assert izq is not sp.espada("N", espejo=False)
    assert sp.escudo(True) is sp.escudo(True)
    assert sp.escudo(True) is not sp.escudo(False)


def test_arma_y_escudo_se_dibujan_del_lado_del_espejo(app):
    """El equipo acompaña el espejo persistente: mirar N con espejo no salta."""
    import dataclasses
    from src.view import capas
    area = pygame.Rect(0, 0, 320, 260)
    centro = (area.w // 2, area.h // 2)
    sup = pygame.Surface(area.size)
    cuerpo = app.sprites.jugador_frame(False, 0, "N", 100, False)[0].get_width() // 2

    def lados(espejo, foto):
        sup.fill((0, 0, 0))
        capas.dibujar_actores(sup, area, foto, app.sprites, app.fuente,
                              facing="N", pos_jugador=centro, espejo=espejo)
        izq = der = 0
        for x in range(area.w):
            for y in range(area.h):
                if sup.get_at((x, y))[:3] == (0, 0, 0):
                    continue
                if x < centro[0] - cuerpo - 4:
                    izq += 1
                elif x > centro[0] + cuerpo + 4:
                    der += 1
        return izq, der

    for item in ("espada-hierro-01", "escudo-madera-01"):
        app.ses.estado.jugador.inventario.append(item)
        assert app.enviar(f"equipar {item}")[0]
        foto = dataclasses.replace(app.foto, enemigos=[])
        izq0, der0 = lados(False, foto)
        izq1, der1 = lados(True, foto)
        assert der0 > 0 and izq0 == 0, item  # sin espejo: a la derecha
        assert izq1 > 0 and der1 == 0, item  # con espejo: a la izquierda


def test_personaje_mira_y_da_el_paso(app):
    from src.view import capas
    assert app.facing == 'N' and app.anim_pasos == 0
    app.enviar('s')
    assert app.facing == 'S' and app.anim_pasos == 8
    assert app.dibujar() is None  # dibujar no retorna foto (solo lee)
    assert app.anim_pasos == 7  # la animacion decae por frame
    for _ in range(8):
        app.dibujar()
    assert app.anim_pasos == 0
    capas.dibujar_actores(app.ventana, app.area_sala(), app.foto,
                          app.sprites, app.fuente, facing='E',
                          desplaza=(4, 0))


# ------------------------------------------------------- prota PNG + Rojo/Azul
def test_jugador_png_frames():
    from src.view.sprites import SpriteManager
    pygame.init()
    sp = SpriteManager()
    assert sp.jugador_png, 'faltan los PNG en assets/sprites/'
    quieto_a, hop0 = sp.jugador_frame(False, 0, total=100)
    quieto_b, hop0b = sp.jugador_frame(False, 99, total=100)
    assert quieto_a is quieto_b and hop0 == hop0b == 0
    parpadeo, hop_p = sp.jugador_frame(False, 0, total=5)
    assert parpadeo is not quieto_a and hop_p == 0  # ojos cerrados, sin salto
    f0, hop_f0 = sp.jugador_frame(True, 0, total=100)
    f1, hop_f1 = sp.jugador_frame(True, 2, total=100)
    assert f0 is quieto_a and f1 is not f0 and hop_f1 == -3 and hop_f0 == 0
    espejo, _ = sp.jugador_frame(False, 0, facing='O')
    normal, _ = sp.jugador_frame(False, 0, facing='E')
    assert espejo.get_size() == normal.get_size()
    assert espejo.get_at((0, 0)) == normal.get_at((normal.get_width() - 1, 0))
    # `espejo` explícito: mirar N/S conservando el volteo horizontal
    izq, _ = sp.jugador_frame(False, 0, facing='N', espejo=True)
    der, _ = sp.jugador_frame(False, 0, facing='N', espejo=False)
    assert izq.get_at((0, 0)) == der.get_at((der.get_width() - 1, 0))


def test_jugador_fallback_sin_png(tmp_path, monkeypatch):
    import src.view.sprites as mod
    from src.view.sprites import SpriteManager
    pygame.init()
    monkeypatch.setattr(mod, 'ASSETS_DIR', tmp_path)
    sp = SpriteManager()
    assert not sp.jugador_png
    img, hop = sp.jugador_frame(True, 2)
    assert hop == 0 and img.get_at((5, 5))[:3] == (70, 130, 230)


def test_icono_ventana_es_el_prota_de_paso():
    from src.view.sprites import SpriteManager
    pygame.init()
    sp = SpriteManager()
    assert sp.jugador_png
    icono = sp.icono()
    assert icono is not sp.jugador          # frame PNG, no el mosaico
    assert icono is sp._jugador_frames[1]   # el mismo que anima el paso
    assert icono.get_height() >= 48         # escala de personaje, no reemplazo


def test_icono_fallback_sin_png(tmp_path, monkeypatch):
    import src.view.sprites as mod
    from src.view.sprites import SpriteManager
    pygame.init()
    monkeypatch.setattr(mod, 'ASSETS_DIR', tmp_path)
    sp = SpriteManager()
    assert sp.icono() is sp.jugador


def test_app_instala_el_icono(tmp_path, monkeypatch):
    from src.view.app import VistaApp
    pygame.init()
    puestos = []
    monkeypatch.setattr(pygame.display, "set_icon",
                        lambda s: puestos.append(s))
    ses = Sesion(backend=FakeBackend(), log_ruta=None,
                 puntajes_ruta=str(tmp_path / "puntajes.jsonl"))
    app = VistaApp(ses, ventana=pygame.Surface((320, 240)))
    assert puestos and puestos[0] is app.sprites.icono()


def test_app_anima_tick_mientras_se_mueve(app):
    tick0 = app.tick_anim
    app.enviar('s')
    app.dibujar()
    assert app.tick_anim == tick0 + 1
    for _ in range(10):
        app.dibujar()
    quieto = app.tick_anim
    app.dibujar()
    assert app.tick_anim == quieto  # quieto: no avanza


# ------------------------------------------------------- movimiento libre
def _teletransportar(app, x, y):
    from src.view import capas  # noqa
    area = app.area_sala()
    app.pos_jugador = [(x - area.x) / area.w, (y - area.y) / area.h]
    app.en_puerta = False


def test_puerta_abierta_cruza_al_llegar(app):
    from src.view import capas
    area = app.area_sala()
    _teletransportar(app, *capas.rect_puerta(area, 'E').center)
    assert app.manejar_tecla(pygame.K_d) == '@paso'
    assert app.foto.sala_id == 2  # cruzo al pisar la puerta, no con la tecla
    assert app.pos_jugador[0] < 0.3  # reaparece por el lado contrario


def test_puerta_cerrada_avisa_y_no_cruza(app):
    from src.view import capas
    app.enviar('e')  # sala 2: puerta S cerrada con llave-hierro-01
    area = app.area_sala()
    _teletransportar(app, *capas.rect_puerta(area, 'S').center)
    assert app.manejar_tecla(pygame.K_s) == '@paso'
    assert app.foto.sala_id == 2
    assert app.aviso and 'cerrada' in app.aviso.lower()


def test_recoger_y_atacar_por_proximidad(app):
    from src.view import capas
    area = app.area_sala()
    assert app.recoger_cercano() is None and app.aviso  # lejos: aviso local
    assert app.atacar_cercano() is None
    _teletransportar(app, *app._spots()[0][0])
    assert app.recoger_cercano() == 'recoger antorcha-01'
    assert app.manejar_tecla(pygame.K_f) == 'recoger antorcha-01'
    assert 'antorcha-01' in app.foto.inventario
    _teletransportar(app, *capas.pos_enemigo(area, 0))
    assert app.atacar_cercano() == 'atacar e1-1'


def test_geometria_dentro_de_sala(app):
    from src.view import capas
    area = app.area_sala()
    for direccion in ('N', 'S', 'E', 'O'):
        assert area.collidepoint(capas.rect_puerta(area, direccion).center)
    assert area.collidepoint(capas.pos_enemigo(area, 0))
    for cx, cy in capas.spots_estaticos(area):
        assert area.collidepoint(cx, cy)


def test_spots_esquivan_puertas_y_banda(app):
    from src.view import capas
    from src.view.sprites import TAM
    area = app.area_sala()
    puertas = [capas.rect_puerta(area, d) for d in ('N', 'S', 'E', 'O')]
    banda = capas.banda_enemiga(area)
    for cx, cy in capas.spots_estaticos(area):
        tile = pygame.Rect(cx - TAM // 2, cy - TAM // 2, TAM, TAM)
        assert area.contains(tile)
        assert not any(tile.colliderect(p) for p in puertas)
        assert not tile.colliderect(banda)


def test_spots_estables_al_recoger_y_al_recargar(app):
    from src.view import capas
    area = app.area_sala()
    memoria = {}
    antes, _ = capas.asignar_spots(area, 1, [], ['a', 'b'], memoria)
    tras_recoger, _ = capas.asignar_spots(area, 1, [], ['b'], memoria)
    assert tras_recoger[0] == antes[1]  # 'b' conserva su puesto
    fresca, _ = capas.asignar_spots(area, 1, [], ['a', 'b'], {})
    assert fresca == antes  # recarga sin memoria: mismo scatter


# ------------------------------------------------------- pelean de vuelta + ritmo
def test_velocidad_manejable():
    from src.view import app as mod
    assert mod.VELOCIDAD * 60 < 0.6  # menos de media sala por segundo


def test_caminar_no_cuesta_vida_ni_tiempo(app):
    vida0 = app.foto.jugador["vida"]
    reloj0 = app.ses.estado.reloj
    for _ in range(48):
        app._paso_libre("n")
    assert app.foto.sala_id == 1  # sin puerta N: camina sin cruzar
    assert app.foto.jugador["vida"] == vida0
    assert app.ses.estado.reloj == reloj0


def test_enemigo_contraataca_tras_atacar(app):
    vida0 = app.foto.jugador["vida"]
    for _ in range(3):  # 3 golpes no matan (7-11 dano vs 40 vida) y drenan
        ok, _, _ = app.enviar("atacar e1-1")
        assert ok
    assert app.foto.jugador["vida"] < vida0  # el guardian devolvio el golpe


# ------------------------------------------------------- feedback de dano
def test_golpe_destella_y_barra_baja(app):
    from src.view import capas, paleta
    from src.view.sprites import TAM
    area = app.area_sala()
    verde = paleta.VIDA

    def verdes():
        cx, cy = capas.pos_enemigo_animada(area, 0, app.tick_total)
        alto = app.sprites.enemigo("").get_height()  # arte compartido x3
        bx, by = cx - TAM // 2, cy - alto // 2 - 10 + 3
        return sum(1 for px in range(bx, bx + TAM)
                   if app.ventana.get_at((px, by))[:3] == verde)

    app.dibujar()
    antes = verdes()
    assert antes == TAM  # vida llena: barra completa
    for _ in range(3):
        ok, _, _ = app.enviar('atacar e1-1')
        assert ok
        app.dibujar()
    assert app.golpe == 'e1-1' and app.golpe_ttl > 0  # destello activo
    assert verdes() < antes  # la barra si baja
    for _ in range(12):
        app.dibujar()
    assert app.golpe is None  # el destello expira


# ------------------------------------------------------- feedback de daño/ataque
def test_dano_tinte_y_sacudida(app):
    from src.view import capas
    base = pygame.Surface((8, 8), pygame.SRCALPHA)
    base.fill((200, 180, 160, 255))
    antes = base.get_at((4, 4))
    rojo = capas._tinte_rojo(base)
    ahora = rojo.get_at((4, 4))
    assert ahora.r >= antes.r and ahora.g < antes.g and ahora.b < antes.b
    assert base.get_at((4, 4)) == antes  # no muta el frame original
    app.dano_ttl = 8
    app.dibujar()  # el tinte y la sacudida se dibujan sin crashear
    assert app.dano_ttl == 7  # y expiran solos


def test_ataque_embiste_siempre_y_taja_con_arma(app):
    ok, _, _ = app.enviar("atacar e1-1")
    assert ok and app.ataque_ttl > 0 and not app.ataque_espada  # embestida
    assert app._empuje_ataque() != (0, 0)  # sin arma ya empujaba
    app.dibujar()
    app.ses.estado.jugador.inventario.append("espada-hierro-01")
    ok, _, _ = app.enviar("equipar espada-hierro-01")
    assert ok
    app.facing = "E"
    ok, _, _ = app.enviar("atacar e1-1")
    assert ok and app.ataque_espada and app.ataque_dir == "E"  # estela
    assert app._empuje_ataque()[0] > 0  # y la embestida también va con arma
    app.dibujar()


def test_tajo_estela_visible_y_expira():
    from src.view import capas
    zona = [(x, y) for x in range(30, 130, 2) for y in range(30, 130, 2)]
    sup = pygame.Surface((160, 160), pygame.SRCALPHA)
    capas.dibujar_tajo(sup, (80, 80), "E", 1.0)
    pintados = [sup.get_at(p) for p in zona if sup.get_at(p)[3] > 0]
    assert pintados
    assert all(c.r == c.g == c.b == 255 for c in pintados)  # estela blanca
    sup2 = pygame.Surface((160, 160), pygame.SRCALPHA)
    capas.dibujar_tajo(sup2, (80, 80), "N", 0.0)
    assert not any(sup2.get_at(p)[3] for p in zona)


# ------------------------------------------------------- trampas al caminar
def test_caminar_sobre_trampa_la_dispara(app):
    """Mejoras 2026-10: pasar por encima de una trampa armada hace daño."""
    from src.view import capas
    area = app.area_sala()
    _, trampas = app._spots()
    assert len(trampas) == 2  # sala 1: t1-1 pinchos + t1-2 llamas
    puertas = [capas.rect_puerta(area, d) for d in ("N", "S", "E", "O")]

    def lejos(p):
        return min(((p[0] - r.centerx) ** 2 + (p[1] - r.centery) ** 2) ** 0.5
                   for r in puertas)

    idx = max(range(len(trampas)), key=lambda i: lejos(trampas[i]))
    cx, cy = trampas[idx]
    inst = app.foto.trampas[idx]["instancia"]
    app.pos_jugador = [(cx - area.x) / area.w, (cy - area.y) / area.h]
    vida0 = app.foto.jugador["vida"]
    app._paso_libre("n")
    assert app.foto.jugador["vida"] < vida0  # el motor aplicó el daño
    assert app.dano_ttl > 0                  # destello rojo
    assert app.trampa_pisada == inst
    assert inst in app.trampas_fuego         # chispazo en su puesto
    # parado encima no se repite: hay que salir del radio y volver a pisarla
    vida1 = app.foto.jugador["vida"]
    for _ in range(3):
        app._paso_libre("n")
    assert app.foto.jugador["vida"] == vida1


def test_trampa_al_entrar_marca_chispazo(app):
    """§2.10: el daño al ENTRAR se ve: chispazo en el puesto de la trampa.

    Aunque el motor la rearme antes de la foto (pinchos rearme=3), la
    bitácora `efecto|trampa|<inst>` delata cuál se disparó.
    """
    from src.view import capas
    app.enviar("s")  # sala 3: t3-1 (veneno) se dispara al entrar
    assert app.trampas_fuego.get("t3-1") == 12
    app.dibujar()    # se dibuja y decae
    assert app.trampas_fuego == {"t3-1": 11}
    ok, _, foto = app.enviar("e")  # sala 4 (iluminada): t4-1 pinchos
    assert foto.sala_id == 4 and app.trampas_fuego.get("t4-1") == 12
    assert "al entrar" in (app.aviso or "")  # el aviso dice el origen
    sup = pygame.Surface((80, 80), pygame.SRCALPHA)
    capas.dibujar_fuego_trampa(sup, (40, 40), 1.0)
    pintados = [sup.get_at((x, y)) for x in range(80) for y in range(80)
                if sup.get_at((x, y))[3] > 0]
    assert pintados and all(c.r > 200 and c.g < 200 for c in pintados)
    sup2 = pygame.Surface((80, 80), pygame.SRCALPHA)
    capas.dibujar_fuego_trampa(sup2, (40, 40), 0.0)
    assert not any(sup2.get_at((x, y))[3] for x in range(80) for y in range(80))


# ------------------------------------------------------- sala oscura
def test_sala_oscura_velo_y_antorcha(app):
    from src.view import capas
    assert not app.foto.sala_oscura  # sala 1 está iluminada
    app.enviar("s")                  # sala 3: "Capilla oscura"
    assert app.foto.sala_id == 3 and app.foto.sala_oscura
    assert not capas.antorcha_encendida(app.foto)
    assert "oscura" in (app.aviso or "").lower()  # aviso al entrar
    area = app.area_sala()
    app.pos_jugador = [0.5, 0.5]
    app.dibujar()
    x, y = area.x + 4, area.y + 4
    con_velo = tuple(app.ventana.get_at((x, y))[:3])
    app.ses.estado.jugador.inventario.append("antorcha-01")
    ok, _, _ = app.enviar("usar antorcha-01")
    assert ok and capas.antorcha_encendida(app.foto)
    app.dibujar()
    sin_velo = tuple(app.ventana.get_at((x, y))[:3])
    assert sin_velo != con_velo and sum(sin_velo) > sum(con_velo)


def test_consola_avisa_sala_oscura(app):
    from src.orchestrator import consola
    app.enviar("s")  # sala 3 oscura
    lineas = []
    consola.renderizar(app.foto, salida=lineas.append)
    assert any("oscuridad" in ln and "oscuras" in ln for ln in lineas)
    app.ses.estado.jugador.inventario.append("antorcha-01")
    app.enviar("usar antorcha-01")
    lineas = []
    consola.renderizar(app.foto, salida=lineas.append)
    assert any("iluminada por tu antorcha" in ln for ln in lineas)


# ------------------------------------------------------- enemigos inconfundibles
def test_enemigos_procedurales_sin_png_con_anillo(tmp_path, monkeypatch):
    import src.view.sprites as mod
    pygame.init()
    monkeypatch.setattr(mod, 'ASSETS_DIR', tmp_path)  # sin arte: fallback
    sp = mod.SpriteManager()
    for comp in ('guardián', 'errante', 'rastreador'):
        img = sp.enemigo(comp)
        cols = {img.get_at((x, y))[:3] for x in range(0, 36, 3)
                for y in range(0, 36, 3)}
        assert (255, 255, 255) in cols  # anillo + insignia blancos


def test_arte_png_sin_fondo_para_items_y_errante():
    from src.view.sprites import SpriteManager, TAM, ENEMIGO_ESCALA
    pygame.init()
    sp = SpriteManager()
    errante = sp.enemigo('errante')  # x3: arte grande, lienzo cuadrado
    assert errante.get_size() == (TAM * ENEMIGO_ESCALA, TAM * ENEMIGO_ESCALA)
    lado = TAM * ENEMIGO_ESCALA - 1
    assert errante.get_at((0, 0))[3] == 0
    assert errante.get_at((lado, lado))[3] == 0
    for item_id in ('llave-hierro-01', 'llave-salida-01', 'antorcha-01',
                    'pergamino-01', 'pinchos-01', 'veneno-01'):
        img = sp.sprite(item_id)
        assert img.get_size() == (TAM, TAM)
        assert img.get_at((0, 0))[3] == 0  # PNG transparente, sin fondo


# ------------------------------------------------------- patrullaje visible
def test_patrullaje_y_alcance(app):
    from src.view import capas
    area = app.area_sala()
    a = capas.pos_enemigo_animada(area, 0, 0)
    assert a == capas.pos_enemigo_animada(area, 0, 0)  # determinista
    b = capas.pos_enemigo_animada(area, 0, 30)
    assert a != b  # patrulla visible en sala
    assert abs(a[0] - b[0]) <= 16 and abs(a[1] - b[1]) <= 12
    _teletransportar(app, *capas.pos_enemigo(area, 0))
    assert app.atacar_cercano() == 'atacar e1-1'  # la deriva no rompe alcance
    app.dibujar()  # alcance dibujado, sin crash


def test_raton_interactua_con_botones_de_menu(app):
    """Los botones de todos los menús responden al ratón (clic = tecla)."""
    app.preparar_menu([{"id": CRIPTA_ID, "nombre": "A", "salas": 6,
                        "dificultad": 1}], False)
    app.dibujar()
    # Continuar deshabilitado: no hay hotspot para K_2.
    assert all(tecla != pygame.K_2 for _, tecla in app.hotspots)
    rect_jugar = next(r for r, t in app.hotspots if t == pygame.K_1)
    # Hover: el panel del botón cambia de color con el ratón encima.
    antes = app.ventana.get_at((rect_jugar.x + 5, rect_jugar.centery))
    app.raton_pos = rect_jugar.center
    app.dibujar()
    despues = app.ventana.get_at((rect_jugar.x + 5, rect_jugar.centery))
    assert antes != despues
    # Clic en Jugar -> selección; clic en la primera tarjeta -> partida.
    assert app.manejar_clic(rect_jugar.center) == "@jugar"
    assert app.pantalla == "seleccion"
    app.dibujar()
    assert app.manejar_clic(app.hotspots[0][0].center) == "@jugar"
    assert app.pantalla == "juego" and app.cripta_actual == CRIPTA_ID
    # Pausa: clic en Volver reanuda y clic en Salir al menú vuelve al inicio.
    assert app.manejar_tecla(pygame.K_ESCAPE) == "@pausa"
    app.dibujar()
    rect_volver = next(r for r, t in app.hotspots if t == pygame.K_ESCAPE)
    assert app.manejar_clic(rect_volver.center) == "@volver"
    assert app.pantalla == "juego"
    app.manejar_tecla(pygame.K_ESCAPE)
    app.dibujar()
    rect_menu = next(r for r, t in app.hotspots if t == pygame.K_q)
    assert app.manejar_clic(rect_menu.center) == "@menu"
    assert app.pantalla == "inicio"
    # Error: el botón "Volver al menú" (Esc) también es clicable.
    app.pantalla = "error"
    app.ultimo_error = "prueba"
    app.dibujar()
    rect_esc = next(r for r, t in app.hotspots if t == pygame.K_ESCAPE)
    assert app.manejar_clic(rect_esc.center) == "@menu"
    assert app.pantalla == "inicio"
