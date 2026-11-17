"""Política de inicio: prepara primero y nunca instala sesiones parciales."""

import pytest

from src.models.errors import InicioNoPermitidoError
from src.models.resolubilidad import UbicacionesLlaves
from src.orchestrator.sesion import Sesion
from test_sesion import FakeBackend, nueva_sesion, CRIPTA_ID


def test_negativo_bloquea_sin_crear_estado_y_forzar_conserva_reporte(tmp_path):
    backend = FakeBackend()
    backend.ubicaciones_llaves = lambda *args: UbicacionesLlaves(
        CRIPTA_ID, backend.fake._general.version, True, ())
    ses = nueva_sesion(tmp_path, backend=backend)
    resultado = ses.preparar_inicio(CRIPTA_ID)
    assert resultado.estado == "no_resoluble" and ses.estado is None
    with pytest.raises(InicioNoPermitidoError) as error:
        ses.iniciar(CRIPTA_ID)
    assert error.value.resultado == resultado and ses.estado is None
    assert not (tmp_path / "p.log").exists()
    ses.iniciar(CRIPTA_ID, forzar=True)
    assert ses.estado is not None and ses.reporte_inicio() == resultado


def test_incompleta_no_se_puede_forzar(tmp_path):
    backend = FakeBackend()
    backend.ubicaciones_llaves = lambda *args: UbicacionesLlaves(
        CRIPTA_ID, backend.fake._general.version, False, ())
    ses = nueva_sesion(tmp_path, backend=backend)
    with pytest.raises(InicioNoPermitidoError):
        ses.iniciar(CRIPTA_ID, forzar=True)
    assert ses.estado is None


def test_preparar_no_crea_estado_y_fallo_preserva_partida_previa(tmp_path):
    backend = FakeBackend()
    ses = nueva_sesion(tmp_path, backend=backend)
    ses.iniciar(CRIPTA_ID)
    anterior = ses.estado
    backend.ubicaciones_llaves = lambda *args: UbicacionesLlaves(
        CRIPTA_ID, backend.fake._general.version, False, ())
    ses.preparar_inicio(CRIPTA_ID)
    with pytest.raises(InicioNoPermitidoError):
        ses.iniciar(CRIPTA_ID)
    assert ses.estado is anterior


def test_preparacion_reutiliza_cache_versionada_sin_reconsultar_llaves(tmp_path):
    backend = FakeBackend()
    llamadas = []
    original = backend.ubicaciones_llaves
    def contar(*args):
        llamadas.append(1)
        return original(*args)
    backend.ubicaciones_llaves = contar
    ruta_cache = str(tmp_path / "cache")
    primera = Sesion(backend=backend, cache_ruta=ruta_cache, log_ruta=None)
    r1 = primera.preparar_inicio(CRIPTA_ID)
    assert len(llamadas) == 1
    backend.ubicaciones_llaves = lambda *args: (_ for _ in ()).throw(AssertionError("cache miss"))
    segunda = Sesion(backend=backend, cache_ruta=ruta_cache, log_ruta=None)
    r2 = segunda.preparar_inicio(CRIPTA_ID)
    assert r2 == r1
