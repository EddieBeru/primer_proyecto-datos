"""C1-4: esqueleto_completo une páginas y valida contra salas_total, sin red."""

import pytest

from src.api import endpoints
from src.models.dungeons import DungeonGeneral, PlayerInitial
from src.models.errors import UnexpectedResponseError
from src.models.rooms import Exit, Room, SkeletonPage


def _info(salas_total=3, paginas=2):
    return DungeonGeneral(
        id="c1", version="v1", salas_total=salas_total, paginas=paginas,
        salas_por_pagina=50, sala_inicial=1, sala_salida=3, llave_salida="l",
        presupuesto_solicitudes=9, inventario_max=10,
        jugador=PlayerInitial(vida_max=100, ataque=10, defensa=5, velocidad=10),
    )


PAGS = {
    1: SkeletonPage(pagina=1, total_paginas=2, salas=[
        Room(id=1, nombre="A", salidas={"E": Exit(sala=2)}),
        Room(id=2, nombre="B", salidas={"O": Exit(sala=1)}),
    ]),
    2: SkeletonPage(pagina=2, total_paginas=2, salas=[
        Room(id=3, nombre="C", salidas={"N": Exit(sala=2)}),
    ]),
}


def test_une_paginas_y_no_refetchea_ficha(monkeypatch):
    llamadas = {"info": 0, "pags": []}
    monkeypatch.setattr(
        endpoints, "info_cripta",
        lambda i, b=None: llamadas.__setitem__("info", 1) or _info(),
    )
    monkeypatch.setattr(
        endpoints, "esqueleto",
        lambda i, p=1, b=None: llamadas["pags"].append(p) or PAGS[p],
    )
    plano = endpoints.esqueleto_completo("c1", None, info=_info())

    assert set(plano) == {1, 2, 3}
    assert llamadas == {"info": 0, "pags": [1, 2]}


def test_sin_info_la_fetchea_una_vez(monkeypatch):
    llamadas = {"info": 0}
    monkeypatch.setattr(
        endpoints, "info_cripta",
        lambda i, b=None: llamadas.__setitem__("info", llamadas["info"] + 1) or _info(),
    )
    monkeypatch.setattr(endpoints, "esqueleto", lambda i, p=1, b=None: PAGS[p])
    plano = endpoints.esqueleto_completo("c1")

    assert set(plano) == {1, 2, 3}
    assert llamadas["info"] == 1


def test_conteo_distinto_lanza_error_propio(monkeypatch):
    monkeypatch.setattr(endpoints, "esqueleto", lambda i, p=1, b=None: PAGS[1])
    with pytest.raises(UnexpectedResponseError):
        endpoints.esqueleto_completo("c1", None, info=_info(salas_total=99, paginas=1))
