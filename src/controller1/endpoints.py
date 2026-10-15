from collections.abc import Sequence
import time

from src.controller1.client import Client
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
from src.models.rooms import Room, SkeletonPage
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

# Funciones helpers
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

def esqueleto_completo(id: str, budget=None, info: DungeonGeneral | None = None) -> dict[int, Room]:
    """Devuelve un dict {número de sala: Room} con todas las salas de la cripta.

    Si ya tienes la ficha (p. ej. de iniciar_cripta), pásala en info
    para no gastar otra petición en refetchearla.
    """
    if info is None:
        info = info_cripta(id, budget)
    plano = {}
    for pagina in range(1, info.paginas + 1):
        lote = esqueleto(id, pagina, budget)
        for sala in lote.salas:
            plano[sala.id] = sala
    if len(plano) != info.salas_total:
        raise UnexpectedResponseError(
            f"Se esperaban {info.salas_total} salas, llegaron {len(plano)}"
        )
    return plano

# Funciones de alto nivel
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

# Endpoints de la API
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


def lote_catalogo_auto(ids: Sequence[str], budget=None) -> dict[str, Entidad]:
    """Pide N fichas del catálogo en lotes de máx 10 (endpoint 7).

    - Quita repetidos preservando orden (el API responde 400 si se repiten).
    - Parte en grupos de 10, una petición por grupo (cada una descuenta 1).
    - Retorna dict {id: ficha}. Lista vacía → {} sin peticiones.
    """
    unicos = list(dict.fromkeys(ids))
    if not unicos:
        return {}
    fichas: dict[str, Entidad] = {}
    for i in range(0, len(unicos), 10):
        lote = lote_catalogo(unicos[i:i + 10], budget)
        for entidad in lote.entidades:
            fichas[entidad.id] = entidad
    return fichas

def ficha_catalogo(id: str, budget=None) -> Entidad:
    def _pedir():
        payload = client.make_request(f"catalogo/{id}")
        return _parse_entidad(payload)

    return _pedir_con_reintento(budget, _pedir)
