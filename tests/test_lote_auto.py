"""C1-5: lote_catalogo_auto parte en lotes de 10, sin repetidos, sin red."""

from src.adapters.budget import BudgetAdapter
from src.api import endpoints
from src.models.catalog import CatalogoResponse


def test_25_ids_hacen_3_peticiones(monkeypatch):
    qs_list = []

    def fake_make_request(endpoint, model=None):
        qs_list.append(endpoint)
        ids = endpoint.split("ids=")[1].split(",")
        return CatalogoResponse.from_dict({
            "entidades": [
                {"id": i, "nombre": i, "peso": 1, "valor": 1, "clase": "antidoto"}
                for i in ids
            ]
        })

    monkeypatch.setattr(endpoints.client, "make_request", fake_make_request)
    ids = [f"obj-{n}" for n in range(25)]
    fichas = endpoints.lote_catalogo_auto(ids)

    assert len(qs_list) == 3
    assert len(qs_list[0].split("ids=")[1].split(",")) == 10
    assert len(qs_list[1].split("ids=")[1].split(",")) == 10
    assert len(qs_list[2].split("ids=")[1].split(",")) == 5
    assert set(fichas) == set(ids)


def test_repetidos_no_provocan_400(monkeypatch):
    vistos = []

    def fake_make_request(endpoint, model=None):
        lote = endpoint.split("ids=")[1].split(",")
        vistos.append(lote)
        assert len(set(lote)) == len(lote), f"repetidos en petición: {lote}"
        return CatalogoResponse.from_dict({
            "entidades": [
                {"id": i, "nombre": i, "peso": 1, "valor": 1, "clase": "antidoto"}
                for i in lote
            ]
        })

    monkeypatch.setattr(endpoints.client, "make_request", fake_make_request)
    fichas = endpoints.lote_catalogo_auto(["a", "b", "a", "c", "b"])

    assert len(vistos) == 1
    assert set(fichas) == {"a", "b", "c"}


def test_vacio_no_pide(monkeypatch):
    llamadas = []

    def fake_make_request(endpoint, model=None):
        llamadas.append(endpoint)
        raise AssertionError("no debió pedir")

    monkeypatch.setattr(endpoints.client, "make_request", fake_make_request)
    assert endpoints.lote_catalogo_auto([]) == {}
    assert llamadas == []


def test_cada_lote_descuenta_budget(monkeypatch):
    def fake_make_request(endpoint, model=None):
        lote = endpoint.split("ids=")[1].split(",")
        return CatalogoResponse.from_dict({
            "entidades": [
                {"id": i, "nombre": i, "peso": 1, "valor": 1, "clase": "antidoto"}
                for i in lote
            ]
        })

    monkeypatch.setattr(endpoints.client, "make_request", fake_make_request)
    budget = BudgetAdapter(presupuesto=9)
    endpoints.lote_catalogo_auto([f"obj-{n}" for n in range(12)], budget)
    assert budget.get_presupuesto() == 7  # 2 lotes
