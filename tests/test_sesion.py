"""Sesión/orquestador: ciclo de vida completo contra backend falso (sin red)."""

import os

import pytest

from src.controller1.unicos import unicos

from src.controller1.fake_provider import CRIPTA_ID, FakeProvider
from src.controller2.bitacora import BitacoraIncompatibleError
from src.orchestrator.sesion import Sesion
from src.models.catalog import CatalogVersion
from src.models.dungeons import DungeonVersion
from src.models.errors import GuardadoError
from src.models.roomContents import ContenidoResponse


class FakeBackend:
    """Endpoints-shape sobre FakeProvider (sin red, sin contar)."""

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
        return {i: self.fake.ficha(i) for i in unicos(ids)}


class FakeBackendContando(FakeBackend):
    """Cuenta lotes de catálogo: distingue red real de almacén en disco."""

    def __init__(self):
        super().__init__()
        self.lotes = 0

    def lote_catalogo_auto(self, ids, budget=None):
        self.lotes += 1
        return super().lote_catalogo_auto(ids, budget)


def nueva_sesion(tmp_path, **kw):
    kw.setdefault("log_ruta", str(tmp_path / "p.log"))
    kw.setdefault("puntajes_ruta", str(tmp_path / "puntajes.jsonl"))
    kw.setdefault("backend", FakeBackend())
    return Sesion(**kw)


RUTA_VICTORIA = ["s", "recoger llave-hierro-01", "e", "abrir N", "n", "abrir S",
                 "s", "s", "o", "recoger llave-salida-01", "abrir E", "e"]


def test_iniciar_deja_foto_y_header(tmp_path):
    ses = nueva_sesion(tmp_path)
    foto = ses.iniciar(CRIPTA_ID, semilla=3)
    assert foto.sala_id == ses.info.sala_inicial and foto.estado == "jugando"
    assert os.path.isfile(str(tmp_path / "p.log"))
    with open(str(tmp_path / "p.log"), encoding="utf-8") as f:
        assert f.readline().startswith("#cripta")


def test_paso_mueve_y_no_crashea_en_invalido(tmp_path):
    ses = nueva_sesion(tmp_path)
    ses.iniciar(CRIPTA_ID)
    ok, _, foto = ses.paso("e")
    assert ok and foto.sala_id == 2
    ok, msg, foto = ses.paso("volar")
    assert not ok and foto.estado == "jugando"


def test_vecinas_precargadas_dormidas_sin_visitar(tmp_path):
    """Mejoras 2026-10: al iniciar, la sala 1 arma sus vecinas (2 y 3)."""
    ses = nueva_sesion(tmp_path)
    ses.iniciar(CRIPTA_ID, semilla=5)
    assert sorted(ses.estado.salas) == [1, 2, 3]  # existen en el modelo…
    assert ses.estado.salas_visitadas == [1]      # …pero no cuentan visita
    assert not any(e.activa for e in ses.estado.salas[2].enemigos)
    assert not any(e.activa for e in ses.estado.salas[3].enemigos)


def test_al_entrar_a_vecina_se_precargan_sus_vecinas(tmp_path):
    ses = nueva_sesion(tmp_path)
    ses.iniciar(CRIPTA_ID, semilla=5)
    ok, _, foto = ses.paso("s")  # sala 3, que ya estaba dormida
    assert ok and foto.sala_id == 3
    assert sorted(ses.estado.salas) == [1, 2, 3, 4, 5]  # vecinas de 3
    assert ses.estado.salas_visitadas == [1, 3]          # sin inflar el puntaje
    assert not any(e.activa for e in ses.estado.salas[5].enemigos)


def test_dormidos_despiertan_al_entrar_con_velocidad_real(tmp_path):
    """Mejoras 2026-10: la activación usa la ficha (antes velocidad 5 fija)."""
    from src.controller2.reloj import intervalo
    ses = nueva_sesion(tmp_path)
    ses.iniciar(CRIPTA_ID, semilla=5)
    dormido = ses.estado.salas[2].enemigos[0]
    assert not dormido.activa and 2 not in ses.estado.salas_visitadas
    ok, _ = ses.fachada.mover("E")  # sin drenar: se ve el evento recién creado
    assert ok and dormido.activa
    vel = ses.proveedor.catalogo["murcielago-errante-01"].velocidad
    assert vel == 12
    ev = next(e for e in ses.fachada.agenda
              if e.tipo == "turno" and (e.datos or {}).get("actor") == "e2-1")
    assert ev.t == intervalo(100, vel)  # 833 con la ficha, no 2000 con vel 5


def test_errante_cruza_desde_sala_vecina(tmp_path):
    """Mejoras 2026-10: el murciélago despierto pasea por el mapa cargado."""
    ses = nueva_sesion(tmp_path)
    ses.iniciar(CRIPTA_ID, semilla=5)
    ses.paso("e")  # 1->2: despierta al murciélago errante (e2-1)
    ses.paso("o")  # vuelve a 1; 2 ya no tiene al jugador
    for _ in range(4):
        ses.paso("esperar")
    murcielago = next((e for s in ses.estado.salas.values()
                       for e in s.enemigos if e.instancia == "e2-1"), None)
    assert murcielago is not None and murcielago.activa
    assert murcielago.sala_actual == 1  # única salida abierta de la armería


def test_rastreadora_sigue_el_rastro_entre_salas(tmp_path):
    """Mejoras 2026-10: la sombra persigue la sala con el rastro más reciente."""
    ses = nueva_sesion(tmp_path)
    ses.iniciar(CRIPTA_ID, semilla=5)
    ses.paso("s")  # 1->3: despierta la sombra rastreadora (e3-1)
    ses.paso("n")  # vuelve a 1: el rastro queda en la entrada
    for _ in range(4):
        ses.paso("esperar")
    sombra = next((e for s in ses.estado.salas.values()
                   for e in s.enemigos if e.instancia == "e3-1"), None)
    assert sombra is not None and sombra.activa
    assert sombra.sala_actual == 1


def test_pergamino_devuelve_a_la_sala_anterior(tmp_path):
    """§2.11: el retroceso deja el estado justo antes de la ultima accion."""
    ses = nueva_sesion(tmp_path)
    ses.iniciar(CRIPTA_ID, semilla=1)
    ses.fachada.estado.jugador.inventario.append("pergamino-01")
    for cmd in ("s", "s"):  # 1 -> 3 -> 5 (a la sala 5 se baja a recogerlo)
        ok, msg, _ = ses.paso(cmd)
        assert ok, msg
    assert ses.estado.sala_actual == 5
    antes = (ses.estado.sala_actual, ses.estado.jugador.vida_actual,
             int(ses.estado.reloj), dict(ses.estado.jugador.efectos))
    ok, msg, _ = ses.paso("n")  # 5 -> 3: la trampa de veneno vuelve a morder
    assert ok and ses.estado.sala_actual == 3
    assert ses.estado.jugador.vida_actual < antes[1]
    ok, msg, foto = ses.paso("deshacer")
    assert ok, msg
    assert foto.sala_id == antes[0] == 5
    assert ses.estado.jugador.vida_actual == antes[1]
    assert int(ses.estado.reloj) == antes[2]
    assert dict(ses.estado.jugador.efectos) == antes[3]
    assert foto.pergaminos == 0  # el pergamino usado quedo consumido (§2.11)


def _retrato_comparable(ses):
    """Estado observable para comparar partidas: sin azar, pila ni marcadores."""
    est = ses.estado
    marcador = lambda ev: ev.tipo == "turno" and (ev.datos or {}).get("kind") == "jugador"
    salas = {}
    for sid in est.salas_visitadas:
        s = est.salas[sid]
        salas[sid] = (
            tuple(s.objetos_suelo),
            tuple((t.instancia, t.tipo_id, bool(t.armada)) for t in s.trampas),
            tuple(sorted((e.instancia, e.tipo_id, e.sala_actual, e.vida_actual,
                          bool(e.activa)) for e in s.enemigos)),
            s.ultima_visita, bool(s.visitada), bool(s.oscura),
        )
    return (
        est.estado, est.sala_actual, bool(est.puerta_salida_abierta),
        est.jugador.vida_actual, dict(est.jugador.efectos),
        sorted(i for i in est.jugador.inventario if "pergamino" not in i),
        est.jugador.arma_equipada, est.jugador.armadura_equipada,
        int(est.reloj), est.acciones_jugador, est.enemigos_derrotados,
        tuple(est.salas_visitadas), salas,
        tuple(sorted((ev.t, ev.tipo, repr(sorted((ev.datos or {}).items())))
                     for ev in ses.fachada.agenda if not marcador(ev))),
    )


def test_seis_acciones_deshacer_cinco_vuelve_al_estado_de_la_primera(tmp_path):
    """C2-9: tras 6 acciones y 5 retrocesos el estado coincide con el de la 1.ª."""
    for sub in ("dirigir", "quedarse"):
        (tmp_path / sub).mkdir()
    a = nueva_sesion(tmp_path / "dirigir")
    b = nueva_sesion(tmp_path / "quedarse")
    a.iniciar(CRIPTA_ID, semilla=1)
    b.iniciar(CRIPTA_ID, semilla=1)
    # El objeto del test es la reversión, no la supervivencia: vida holgada.
    for ses in (a, b):
        ses.estado.jugador.vida_max = ses.estado.jugador.vida_actual = 300
    for _ in range(5):
        a.fachada.estado.jugador.inventario.append("pergamino-01")
    for i, cmd in enumerate(["s", "n", "s", "n", "s", "n"]):  # 1 <-> 3
        ok, msg, _ = a.paso(cmd)
        assert ok, (cmd, msg)
        if i == 0:
            ok, msg, _ = b.paso(cmd)
            assert ok, (cmd, msg)
    for _ in range(5):
        ok, msg, _ = a.paso("deshacer")
        assert ok, msg
    assert a.fachada.foto().pergaminos == 0  # los 5 usados, consumidos
    assert _retrato_comparable(a) == _retrato_comparable(b)


def test_victoria_completa_y_finalizar(tmp_path):
    ses = nueva_sesion(tmp_path)
    ses.iniciar(CRIPTA_ID)
    for cmd in RUTA_VICTORIA:
        ok, msg, _ = ses.paso(cmd)
        assert ok, (cmd, msg)
    assert ses.estado.estado == "victoria"
    res = ses.finalizar()
    assert res["terminada"] is True and res["estado"] == "victoria"
    assert "red" in res and os.path.isfile(str(tmp_path / "puntajes.jsonl"))


def test_ficha_desalojada_se_recupera_sin_red(tmp_path):
    """§4.4: si la LRU desaloja una ficha, el almacén la devuelve sin red."""
    be = FakeBackendContando()
    ses = nueva_sesion(tmp_path, backend=be, cache_size=2,
                       cache_ruta=str(tmp_path / "cache.pkl"))
    ses.iniciar(CRIPTA_ID, semilla=3)
    lotes = be.lotes
    assert lotes >= 1 and ses.almacen is not None

    ses.estado.salas.clear()  # fuerza rearmar salas y pedir fichas de nuevo
    ses.proveedor.catalogo.clear()
    ses.loader._contenido.clear()
    ses.loader.sala_lista(1)

    assert be.lotes == lotes            # ninguna ficha volvió a la red
    assert ses.budget.reporte()["disco"] > 0


def test_almacen_sobrevive_al_cierre_de_sesion(tmp_path):
    """§4.3: reabrir no re-pide el catálogo si la versión no cambió."""
    ruta_cache = str(tmp_path / "cache.pkl")
    ses = nueva_sesion(tmp_path, cache_ruta=ruta_cache)
    ses.iniciar(CRIPTA_ID, semilla=3)

    os.remove(ruta_cache)  # la caché en memoria se perdió al "cerrar"
    be2 = FakeBackendContando()
    ses2 = nueva_sesion(tmp_path, backend=be2, cache_ruta=ruta_cache)
    ses2.iniciar(CRIPTA_ID, semilla=3)

    assert be2.lotes == 0
    assert os.path.isfile(ruta_cache + ".fichas")
    assert ses2.budget.reporte()["disco"] > 0


def test_inventario_ordenado_por_criterio(tmp_path):
    """§4.5: copia ordenada con los sorts de C1; el inventario real no se toca."""
    ses = nueva_sesion(tmp_path)
    ses.iniciar(CRIPTA_ID)
    real = ["espada-hierro-01", "antorcha-01", "pocion-roja-01"]
    ses.fachada.estado.jugador.inventario = list(real)
    ses._recargar_catalogo()

    assert ses.inventario_ordenado() == real
    assert ses.inventario_ordenado("peso") == ["pocion-roja-01", "antorcha-01",
                                               "espada-hierro-01"]
    assert ses.inventario_ordenado("valor") == ["antorcha-01", "pocion-roja-01",
                                                "espada-hierro-01"]
    assert ses.fachada.estado.jugador.inventario == real  # sin mutar


def test_consola_lista_inventario_ordenado(tmp_path):
    from src.orchestrator import consola
    ses = nueva_sesion(tmp_path)
    ses.iniciar(CRIPTA_ID)
    ses.fachada.estado.jugador.inventario = ["espada-hierro-01", "pocion-roja-01"]
    ses._recargar_catalogo()
    lineas: list[str] = []
    entradas = iter(["inventario peso", "salir"])
    codigo = consola.bucle(ses, entrada=lambda _p="": next(entradas),
                           salida=lineas.append)
    assert codigo == 0
    assert "inv (peso): pocion-roja-01, espada-hierro-01" in lineas


def test_guardar_cargar_roundtrip(tmp_path):
    ses = nueva_sesion(tmp_path)
    ses.iniciar(CRIPTA_ID)
    ses.paso("e")
    ruta = str(tmp_path / "p.bin")
    ses.guardar(ruta)
    ses2 = nueva_sesion(tmp_path, log_ruta=str(tmp_path / "p2.log"))
    foto = ses2.cargar_en_frio(ruta)
    assert foto.sala_id == ses.estado.sala_actual == 2
    assert foto.presupuesto == ses.foto().presupuesto


def test_replay_reproduce_mismo_estado(tmp_path):
    ses = nueva_sesion(tmp_path)
    ses.iniciar(CRIPTA_ID, semilla=5)
    for cmd in ["e", "o", "s"]:
        ses.paso(cmd)
    sala = ses.estado.sala_actual
    ses2 = nueva_sesion(tmp_path, log_ruta=str(tmp_path / "r2.log"))
    foto = ses2.reproducir(str(tmp_path / "p.log"))
    assert foto.sala_id == sala


def test_replay_version_incompatible(tmp_path):
    ses = nueva_sesion(tmp_path)
    ses.iniciar(CRIPTA_ID)
    ses.paso("e")
    log = str(tmp_path / "p.log")
    with open(log, encoding="utf-8") as f:
        lineas = f.readlines()
    lineas[0] = "#cripta otra v9 v9 0\n"
    malo = str(tmp_path / "malo.log")
    with open(malo, "w", encoding="utf-8") as f:
        f.writelines(lineas)
    ses2 = nueva_sesion(tmp_path, log_ruta=str(tmp_path / "r3.log"))
    with pytest.raises(BitacoraIncompatibleError):
        ses2.reproducir(malo)


def test_cargar_versiones_distintas_falla(tmp_path, monkeypatch):
    from src.controller1 import savegame
    ses = nueva_sesion(tmp_path)
    ses.iniciar(CRIPTA_ID)
    ruta = str(tmp_path / "p.bin")
    ses.guardar(ruta)
    monkeypatch.setattr(savegame, "validar_versiones", lambda *a, **k: (False, True))
    ses2 = nueva_sesion(tmp_path, log_ruta=str(tmp_path / "p4.log"))
    ses2.iniciar(CRIPTA_ID)
    with pytest.raises(GuardadoError):
        ses2.cargar(ruta)


def test_backends_cumplen_protocolo():
    import src.controller1.endpoints as ep
    from src.controller1.offline import OfflineBackend
    for b in (ep, OfflineBackend):
        for m in ("info_cripta", "version_cripta", "version_catalogo",
                  "esqueleto_completo", "contenido", "lote_catalogo_auto"):
            assert hasattr(b, m), (b, m)
