"""C1-3: budget descuenta por intento, 429 reintenta, resto propaga, sin red."""

import pytest

from src.adapters.budget import BudgetAdapter
from src.api import endpoints
from src.models.errors import NotFoundError, PresupuestoAgotadoError, RateLimitedError


def test_exito_descuenta_uno(monkeypatch):
    monkeypatch.setattr(endpoints.client, "make_request", lambda *a, **k: "ok")
    budget = BudgetAdapter(presupuesto=9)
    assert endpoints.listar_criptas(budget) == "ok"
    assert budget.get_presupuesto() == 8


def test_429_reintenta_y_espera_reintentar_en(monkeypatch):
    n = {"i": 0}

    def flaky(*a, **k):
        n["i"] += 1
        if n["i"] == 1:
            raise RateLimitedError("ocupado", 2)
        return "ok"

    monkeypatch.setattr(endpoints.client, "make_request", flaky)
    esperas = []
    budget = BudgetAdapter(presupuesto=9)
    assert endpoints._pedir_con_reintento(budget, lambda: endpoints.client.make_request(),
                                          esperar_fn=lambda s: esperas.append(s)) == "ok"
    assert budget.get_presupuesto() == 7
    assert esperas == [2]


def test_404_no_reintenta(monkeypatch):
    def roto(*a, **k):
        raise NotFoundError("no existe")

    monkeypatch.setattr(endpoints.client, "make_request", roto)
    budget = BudgetAdapter(presupuesto=9)
    with pytest.raises(NotFoundError):
        endpoints.listar_criptas(budget)
    assert budget.get_presupuesto() == 8


def test_agotado_no_toca_red(monkeypatch):
    llamadas = []
    monkeypatch.setattr(endpoints.client, "make_request",
                        lambda *a, **k: llamadas.append(1) or "x")
    budget = BudgetAdapter(presupuesto=1)
    budget.gastar()
    with pytest.raises(PresupuestoAgotadoError):
        endpoints.listar_criptas(budget)
    assert llamadas == []


def test_429_persistente_consume_max_intentos(monkeypatch):
    monkeypatch.setattr(endpoints.client, "make_request",
                        lambda *a, **k: (_ for _ in ()).throw(RateLimitedError("x", 1)))
    budget = BudgetAdapter(presupuesto=10)
    with pytest.raises(RateLimitedError):
        endpoints._pedir_con_reintento(budget, lambda: endpoints.client.make_request(),
                                        max_intentos=2, esperar_fn=lambda s: None)
    assert budget.get_presupuesto() == 8


def test_reiniciar_con_total_api():
    budget = BudgetAdapter(presupuesto=14)
    budget.reiniciar(9)
    assert budget.get_presupuesto() == 9
    assert budget.puede_mas()
