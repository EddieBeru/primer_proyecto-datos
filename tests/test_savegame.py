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


@pytest.mark.parametrize('version', [1, 2])
def test_p2_rechaza_versiones_anteriores(tmp_path, version):
    ruta = tmp_path/'vieja.bin'
    ruta.write_bytes(savegame.MAGIA + bytes([version]) + b'contenido legado')
    with pytest.raises(GuardadoError, match='incompatib'):
        savegame.cargar_p2(str(ruta))


def test_historia_v4_conserva_y_valida_conocimiento(tmp_path):
    """FR-NIE-08 (T052): la historia v4 conserva el conocimiento; la carga lo valida."""
    from copy import deepcopy
    from test_sesion import CRIPTA_ID, nueva_sesion
    ses = nueva_sesion(tmp_path, checkpoint_cada=2)
    ses.iniciar(CRIPTA_ID, semilla=7)
    ses.proveedor.catalogo.update(ses.backend.fake._fichas)
    ses.estado.jugador.inventario.extend(['antorcha-01', 'pergamino-01'])
    assert ses.paso('usar antorcha-01')[0] and ses.paso('s')[0]
    ruta = str(tmp_path/'v4-t052.bin')
    ses.guardar(ruta)
    historia = ses.linea.a_dict()
    mapas = [ses.historia_accion(i).mapa for i in (1, 2)]
    # Roundtrip válido: la historia completa sigue reconstruyendo el conocimiento.
    ses.cargar_en_frio(ruta)
    assert ses.linea.a_dict() == historia
    assert [ses.historia_accion(i).mapa for i in (1, 2)] == mapas
    actual = ses.estado.a_dict()
    # El conocimiento del guardado se valida contra metadatos vivos.
    data = savegame.cargar_historia(ruta)
    mal = deepcopy(data)
    next(r for r in mal['conocimiento']['salas'] if r['estado'] == 'explorada')['nombre'] = 'Falso'
    falsa = str(tmp_path/'conocimiento-falso.bin')
    savegame.guardar(falsa, mal)
    with pytest.raises(GuardadoError, match='conocimiento inválido'):
        ses.cargar(falsa)
    assert ses.estado.a_dict() == actual and ses.linea.a_dict() == historia
    # Un checkpoint histórico alterado tampoco se instala.
    mal = deepcopy(data)
    mal['historia']['checkpoints'][-1][2]['conocimiento']['salas'] = []
    falsa = str(tmp_path/'checkpoint-falso.bin')
    savegame.guardar(falsa, mal)
    with pytest.raises(GuardadoError, match='historia inválida'):
        ses.cargar(falsa)
    assert ses.estado.a_dict() == actual and ses.linea.a_dict() == historia
