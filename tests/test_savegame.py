"""C1-8: guardado binario ida-vuelta, dañado amable, versiones, sin red."""

import pytest

from src.controller1 import savegame
from src.controller1 import endpoints
from src.models.errors import GuardadoError


ESTADO = {
    "cripta_id": "c1", "version_cripta": "v1", "version_catalogo": "k3",
    "sala_actual": 4, "vida": 70, "vida_max": 100, "ataque": 10,
    "defensa": 5, "velocidad": 8, "presupuesto": 6,
    "inventario": ["espada-hierro-01", "pocion-roja-01"],
}


def test_ida_y_vuelta(tmp_path):
    ruta = str(tmp_path / "partida.bin")
    savegame.guardar(ruta, ESTADO)
    assert savegame.cargar(ruta) == ESTADO


def test_inventario_vacio(tmp_path):
    ruta = str(tmp_path / "p.bin")
    e = dict(ESTADO, inventario=[])
    savegame.guardar(ruta, e)
    assert savegame.cargar(ruta) == e


def test_truncado_y_basura_no_crashean(tmp_path):
    ruta = str(tmp_path / "p.bin")
    savegame.guardar(ruta, ESTADO)
    with open(ruta, "rb") as f:
        bueno = f.read()
    with open(ruta, "wb") as f:
        f.write(bueno[:10])  # truncado
    with pytest.raises(GuardadoError):
        savegame.cargar(ruta)
    with open(ruta, "wb") as f:
        f.write(b"basura total")
    with pytest.raises(GuardadoError):
        savegame.cargar(ruta)


def test_inexistente_error_amable(tmp_path):
    with pytest.raises(GuardadoError):
        savegame.cargar(str(tmp_path / "nada.bin"))


def test_validar_versiones(monkeypatch):
    from src.models.dungeons import DungeonVersion
    from src.models.catalog import CatalogVersion
    monkeypatch.setattr(endpoints, "version_cripta",
                        lambda i, b=None: DungeonVersion(id=i, version="v1"))
    monkeypatch.setattr(endpoints, "version_catalogo",
                        lambda b=None: CatalogVersion(version="k9"))
    assert savegame.validar_versiones(ESTADO) == (True, False)
