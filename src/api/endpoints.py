from collections.abc import Sequence

from src.api.client import Client
from src.models.catalog import CatalogVersion, CatalogoResponse, Enemy, Trap
from src.models.dungeons import CriptasResponse, DungeonGeneral, DungeonVersion
from src.models.errors import UnexpectedResponseError
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


def listar_criptas() -> CriptasResponse:
    return client.make_request("criptas", model=CriptasResponse)


def info_cripta(id: str) -> DungeonGeneral:
    return client.make_request(f"criptas/{id}", model=DungeonGeneral)


def version_cripta(id: str) -> DungeonVersion:
    return client.make_request(f"criptas/{id}/version", model=DungeonVersion)


def esqueleto(id: str, pagina: int = 1) -> SkeletonPage:
    if pagina < 1:
        raise ValueError(f"pagina empieza en 1, llegó {pagina}")
    return client.make_request(f"criptas/{id}/salas?pagina={pagina}", model=SkeletonPage)


def contenido(id: str, salas: Sequence[int]) -> ContenidoResponse:
    lote = _validar_lote(salas)
    qs = ",".join(map(str, lote))
    return client.make_request(f"criptas/{id}/contenido?salas={qs}", model=ContenidoResponse)


def version_catalogo() -> CatalogVersion:
    return client.make_request("catalogo/version", model=CatalogVersion)


def lote_catalogo(ids: Sequence[str]) -> CatalogoResponse:
    lote = _validar_lote(ids)
    qs = ",".join(lote)
    return client.make_request(f"catalogo?ids={qs}", model=CatalogoResponse)


def ficha_catalogo(id: str) -> Entidad:
    payload = client.make_request(f"catalogo/{id}")
    return _parse_entidad(payload)
