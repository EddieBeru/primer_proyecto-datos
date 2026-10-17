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


def test_manejar_tecla_mueve_libre_sin_cambiar_sala(app):
    pos0 = list(app.pos_jugador)
    assert app.manejar_tecla(pygame.K_e) is None  # abrir N falla (no hay puerta)
    assert app.manejar_tecla(pygame.K_s) == "@paso"
    assert app.foto.sala_id == 1 and app.facing == "S"  # camina, no cruza
    assert app.pos_jugador[1] > pos0[1]


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
    assert sp.enemigo("guardián").get_at((5, 5)) != \
        sp.enemigo("errante").get_at((5, 5))
    assert sp.puerta(False, None).get_at((5, 5)) != \
        sp.puerta(True, "llave-hierro-01").get_at((5, 5))
    assert sp.puerta(True, None).get_at((5, 5)) != \
        sp.puerta(True, "llave-hierro-01").get_at((5, 5))


# ------------------------------------------------------- pantallas sin crashear
def test_pantallas(app):
    from src.view import pantallas
    sup, fuente = app.ventana, app.fuente
    pantallas.pantalla_inicio(sup, fuente, False)
    pantallas.pantalla_inicio(sup, fuente, True)
    pantallas.pantalla_seleccion(sup, fuente, [
        {"id": "a", "nombre": "A", "salas": 6, "dificultad": 1},
        {"id": "b", "nombre": "B", "salas": 3, "dificultad": 2}])
    pantallas.pantalla_carga(sup, fuente)
    pantallas.pantalla_carga(sup, fuente, "El servidor pide esperar 5 segundos…")
    pantallas.pantalla_juego(sup, fuente, app.foto, app.sprites, app.area_sala())
    pantallas.pantalla_juego(sup, fuente, app.foto, app.sprites, app.area_sala(),
                             dev=True)
    pantallas.menu_pausa(sup, fuente)
    pantallas.pantalla_error(sup, fuente, "Sin conexión.")
    pantallas.pantalla_version(sup, fuente, "Versión anterior.")
    assert isinstance(app.foto, FotoEstado)


def test_pantalla_fin_victoria_y_derrota(app):
    from src.view import pantallas
    for cmd in RUTA_VICTORIA:
        ok, msg, _ = app.enviar(cmd)
        assert ok, (cmd, msg)
    assert app.foto.estado == "victoria" and app.pantalla == "fin"
    reporte = app.finalizar()
    assert reporte["terminada"] is True
    pantallas.pantalla_fin(app.ventana, app.fuente, app.foto, reporte)
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


# ------------------------------------------------------- CLI --vista (C1-10)
def test_cli_vista():
    from src.controller1.cli import parse_args
    assert parse_args([]).vista is False
    assert parse_args(["--vista"]).vista is True


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


def test_jugador_fallback_sin_png(tmp_path, monkeypatch):
    import src.view.sprites as mod
    from src.view.sprites import SpriteManager
    pygame.init()
    monkeypatch.setattr(mod, 'ASSETS_DIR', tmp_path)
    sp = SpriteManager()
    assert not sp.jugador_png
    img, hop = sp.jugador_frame(True, 2)
    assert hop == 0 and img.get_at((5, 5))[:3] == (70, 130, 230)


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
        bx, by = cx - TAM // 2, cy - TAM // 2 - 10 + 3
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


# ------------------------------------------------------- enemigos inconfundibles
def test_enemigos_circulares_con_insignia():
    from src.view.sprites import SpriteManager
    pygame.init()
    sp = SpriteManager()
    for comp in ('guardián', 'errante', 'rastreador'):
        img = sp.enemigo(comp)
        cols = {img.get_at((x, y))[:3] for x in range(0, 36, 3)
                for y in range(0, 36, 3)}
        assert (255, 255, 255) in cols  # anillo + insignia blancos


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
