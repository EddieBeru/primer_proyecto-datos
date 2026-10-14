from collections.abc import Sequence
import time

from src.api.client import Client
from src.models.catalog import CatalogVersion, CatalogoResponse, Enemy, Trap
from src.models.dungeons import CriptasResponse, DungeonGeneral, DungeonVersion
from src.models.errors import RateLimitedError, UnexpectedResponseError
from src.models.objects import (
    Antidote,
    Armor,
    Key,
    Potion,
    RewindScroll,
    Torch,
    Weapon,
)
from src.models.roomContents import ContenidoResponse
from src.models.rooms import SkeletonPage
from src.models.types import Entidad

client = Client()

_PARSERS = {
    "enemigo": Enemy.from_dict,
    "trampa": Trap.from_dict,
    "arma": Weapon.from_dict,
    "armadura": Armor.from_dict,
    "pocion": Potion.from_dict,
    "antidoto": Antidote.from_dict,
    "llave": Key.from_dict,
    "antorcha": Torch.from_dict,
    "pergamino_retroceso": RewindScroll.from_dict,
}

def _pedir_con_reintento(budget, pide, max_intentos=3, esperar_fn=time.sleep):
    """Envuelve una petición con presupuesto + reintento ante 429.

    - Cada intento descuenta 1 vía budget.gastar().
    - PresupuestoAgotadoError sale directo, sin reintentar.
    - Solo RateLimitedError reintenta, esperando max(1, reintentar_en)
      vía esperar_fn (inyectable para no congelar Pygame).
    - Otros errores (404, 500, red) propagan inmediato.
    - budget=None: una sola llamada sin contar (compatibilidad / pruebas).
    """
    if budget is None:
        return pide()
    ultimo = None
    for _ in range(max_intentos):
        budget.gastar()
        try:
            return pide()
        except RateLimitedError as e:
            ultimo = e
            esperar_fn(max(1, e.reintentar_en))
    raise ultimo

def _parse_entidad(payload: dict) -> Entidad:
    try:
        parser = _PARSERS[payload.get("clase", "")]
    except AttributeError as e:
        raise UnexpectedResponseError(f"Ficha sin forma de entidad: {payload!r}") from e
    if parser is None:
        raise UnexpectedResponseError(f"clase desconocida: {payload.get('clase')}")
    try:
        return parser(payload)
    except (KeyError, TypeError, ValueError) as e:
        raise UnexpectedResponseError(f"Ficha inválida: {str(e)}") from e


def _validar_lote(ids: Sequence) -> list:
    ids = list(ids)
    if not 1 <= len(ids) <= 10:
        raise ValueError(f"Lote debe traer 1-10 ids, llegaron {len(ids)}")
    if len(set(ids)) != len(ids):
        raise ValueError("Lote con ids repetidos, API responde 400")
    return ids


def listar_criptas(budget=None) -> CriptasResponse:
    def _pedir():
        return client.make_request("criptas", model=CriptasResponse)

    return _pedir_con_reintento(budget, _pedir)


def info_cripta(id: str, budget=None) -> DungeonGeneral:
    def _pedir():
        return client.make_request(f"criptas/{id}", model=DungeonGeneral)

    return _pedir_con_reintento(budget, _pedir)


def version_cripta(id: str, budget=None) -> DungeonVersion:
    def _pedir():
        return client.make_request(f"criptas/{id}/version", model=DungeonVersion)

    return _pedir_con_reintento(budget, _pedir)


def esqueleto(id: str, pagina: int = 1, budget=None) -> SkeletonPage:
    if pagina < 1:
        raise ValueError(f"pagina empieza en 1, llegó {pagina}")

    def _pedir():
        return client.make_request(f"criptas/{id}/salas?pagina={pagina}", model=SkeletonPage)

    return _pedir_con_reintento(budget, _pedir)


def contenido(id: str, salas: Sequence[int], budget=None) -> ContenidoResponse:
    lote = _validar_lote(salas)
    qs = ",".join(map(str, lote))

    def _pedir():
        return client.make_request(f"criptas/{id}/contenido?salas={qs}", model=ContenidoResponse)

    return _pedir_con_reintento(budget, _pedir)


def version_catalogo(budget=None) -> CatalogVersion:
    def _pedir():
        return client.make_request("catalogo/version", model=CatalogVersion)

    return _pedir_con_reintento(budget, _pedir)


def lote_catalogo(ids: Sequence[str], budget=None) -> CatalogoResponse:
    lote = _validar_lote(ids)
    qs = ",".join(lote)

    def _pedir():
        return client.make_request(f"catalogo?ids={qs}", model=CatalogoResponse)

    return _pedir_con_reintento(budget, _pedir)


def ficha_catalogo(id: str, budget=None) -> Entidad:
    def _pedir():
        payload = client.make_request(f"catalogo/{id}")
        return _parse_entidad(payload)

    return _pedir_con_reintento(budget, _pedir)
