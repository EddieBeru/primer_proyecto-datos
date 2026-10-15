"""Sesión/orquestador: ciclo de vida completo contra backend falso (sin red)."""

import os

import pytest

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
        return {i: self.fake.ficha(i) for i in dict.fromkeys(ids)}


def nueva_sesion(tmp_path, **kw):
    kw.setdefault("log_ruta", str(tmp_path / "p.log"))
    kw.setdefault("puntajes_ruta", str(tmp_path / "puntajes.jsonl"))
    return Sesion(backend=FakeBackend(), **kw)


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
