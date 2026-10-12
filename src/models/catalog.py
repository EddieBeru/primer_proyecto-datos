from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal, Optional

if TYPE_CHECKING:
    from models.types import Entidad

@dataclass
class Enemy:
    id: str
    nombre: str
    vida_max: int  # > 0
    ataque: int
    defensa: int
    velocidad: int  # > 0
    comportamiento: Literal["guardián", "errante", "rastreador"]
    suelta: Optional[list[str]] = None
    clase: str = field(default="enemigo", init=False)

@dataclass
class Trap:
    id: str
    nombre: str
    daño: int
    rearme: Optional[int] = None
    clase: str = field(default="trampa", init=False)

@dataclass
class CatalogoResponse:
    entidades: list["Entidad"] = field(default_factory=list)

@dataclass
class CatalogVersion:
    version: str