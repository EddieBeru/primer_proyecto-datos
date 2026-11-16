"""Contrato HTTP de ubicaciones con transporte simulado."""

import pytest

from src.controller1 import endpoints
from src.controller1.budget import BudgetAdapter
from src.models.errors import RateLimitedError, PresupuestoAgotadoError
from src.models.errors import NotFoundError, NetworkError


def test_parsea_orden_y_cuenta_reintento_429(monkeypatch):
    respuestas = iter([RateLimitedError("ocupado", 1), {
        "cripta_id": "c", "version_cripta": "v", "completa": True,
        "llaves": [{"id": "Z", "sala": 2, "enemigo": "e"},
                   {"id": "A", "sala": 1, "enemigo": None}]}]
    )
    llamadas = []
    def pedir(url):
        llamadas.append(url)
        item = next(respuestas)
        if isinstance(item, Exception):
            raise item
        return item
    monkeypatch.setattr(endpoints.client, "make_request", lambda endpoint, **kw: pedir(endpoint))
    monkeypatch.setattr(endpoints.time, "sleep", lambda _: None)
    budget = BudgetAdapter(3)
    resultado = endpoints.ubicaciones_llaves("c", budget, "v")
    assert [x.id for x in resultado.llaves] == ["Z", "A"]
    assert budget.reporte()["realizadas"] == 2


def test_budget_agotado_no_hace_peticion(monkeypatch):
    llamadas = []
    monkeypatch.setattr(endpoints.client, "make_request", lambda *a, **k: llamadas.append(a))
    with pytest.raises(PresupuestoAgotadoError):
        endpoints.ubicaciones_llaves("c", BudgetAdapter(0), "v")
    assert llamadas == []


def test_respuesta_incompleta_no_se_confunde_con_lista_vacia_completa(monkeypatch):
    monkeypatch.setattr(endpoints.client, "make_request", lambda *a, **k: {
        "cripta_id": "c", "version_cripta": "v", "completa": False,
        "llaves": []})
    respuesta = endpoints.ubicaciones_llaves("c", None, "v")
    assert respuesta.completa is False and respuesta.llaves == ()


def test_forma_legada_del_endpoint_se_adapta_con_version_validada(monkeypatch):
    monkeypatch.setattr(endpoints.client, "make_request", lambda *a, **k: {
        "llaves": [{"id": "k", "sala": 2}]})
    respuesta = endpoints.ubicaciones_llaves("c", None, "v")
    assert respuesta.cripta_id == "c"
    assert respuesta.version_cripta == "v"
    assert respuesta.completa is True
    assert [(x.id, x.sala) for x in respuesta.llaves] == [("k", 2)]


def test_forma_legada_no_infiere_version_si_no_hay_contexto(monkeypatch):
    monkeypatch.setattr(endpoints.client, "make_request", lambda *a, **k: {
        "llaves": [{"id": "k", "sala": 2}]})
    with pytest.raises(Exception, match="versión validada"):
        endpoints.ubicaciones_llaves("c")


def test_tipos_estrictos_rechazan_bool_como_sala(monkeypatch):
    monkeypatch.setattr(endpoints.client, "make_request", lambda *a, **k: {
        "cripta_id": "c", "version_cripta": "v", "completa": True,
        "llaves": [{"id": "k", "sala": True, "enemigo": None}]})
    with pytest.raises(Exception, match="sala"):
        endpoints.ubicaciones_llaves("c", None, "v")


def test_rechaza_mismatch_de_version(monkeypatch):
    monkeypatch.setattr(endpoints.client, "make_request", lambda *a, **k: {
        "cripta_id": "c", "version_cripta": "antigua", "completa": True,
        "llaves": []})
    with pytest.raises(Exception, match="versión"):
        endpoints.ubicaciones_llaves("c", None, "actual")


@pytest.mark.parametrize("error", [NotFoundError("404"), NetworkError("sin red")])
def test_fallos_de_transporte_no_se_convierten_en_lista_vacia(monkeypatch, error):
    monkeypatch.setattr(endpoints.client, "make_request", lambda *a, **k: (_ for _ in ()).throw(error))
    with pytest.raises(type(error)):
        endpoints.ubicaciones_llaves("c", BudgetAdapter(1), "v")
