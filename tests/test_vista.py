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
                  "__future__", "dataclasses", "os", "typing"}
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
    assert intencion_para_tecla(pygame.K_SPACE, foto, "N") == "atacar e1-1"
    assert intencion_para_tecla(pygame.K_f, foto, "N") == "recoger antorcha-01"
    assert intencion_para_tecla(pygame.K_u, foto, "N") == "deshacer"
    assert intencion_para_tecla(pygame.K_TAB, foto, "N") == "@tab-inv"
    assert intencion_para_tecla(pygame.K_t, foto, "N") == "@tab-suelo"
    assert intencion_para_tecla(pygame.K_F1, foto, "N") == "@dev"
    assert intencion_para_tecla(pygame.K_g, foto, "N") == "@guardar"
    assert intencion_para_tecla(pygame.K_ESCAPE, foto, "N") == "@pausa"
    assert intencion_para_tecla(pygame.K_1, foto, "N") == "@enemigo+0"
    assert intencion_para_tecla(pygame.K_F5, foto, "N") is None


def test_manejar_tecla_mueve_y_gira(app):
    assert app.manejar_tecla(pygame.K_e) in (None, "abrir E", "abrir N")
    assert app.manejar_tecla(pygame.K_s) == "s"
    assert app.foto.sala_id == 3 and app.facing == "s"


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
