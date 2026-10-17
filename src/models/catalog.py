from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal, Optional

if TYPE_CHECKING:
    from src.models.types import Entidad

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

    @classmethod
    def from_dict(cls, data: dict) -> "Enemy":
        return cls(
            id=data["id"],
            nombre=data["nombre"],
            vida_max=data["vida_max"],
            ataque=data["ataque"],
            defensa=data["defensa"],
            velocidad=data["velocidad"],
            comportamiento=data["comportamiento"],
            suelta=data.get("suelta"),
        )

def _pulso(valor) -> Optional[int]:
    """Campo opcional de efecto (``veneno``/``quemadura``): None si no viene,
    cantidad de daño por pulso si viene (``true`` = 1)."""
    if valor is None or valor is False:
        return None
    return max(1, int(valor))


@dataclass
class Trap:
    id: str
    nombre: str
    dano: int
    rearme: Optional[int] = None
    # Efectos extra opcionales (mejoras 2026-10): daño por pulso.
    veneno: Optional[int] = None      # pulsos cada 80 durante 400 (§2.10)
    quemadura: Optional[int] = None   # pulsos propios; no la cura el antídoto
    clase: str = field(default="trampa", init=False)

    @classmethod
    def from_dict(cls, data: dict) -> "Trap":
        return cls(
            id=data["id"],
            nombre=data["nombre"],
            dano=int(data.get("daño", 0) or 0),
            rearme=data.get("rearme"),
            veneno=_pulso(data.get("veneno")),
            quemadura=_pulso(data.get("quemadura", data.get("fuego"))),
        )

@dataclass
class CatalogoResponse:
    entidades: list["Entidad"] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "CatalogoResponse":
        # Import local para evitar ciclo con models.types
        from src.models.objects import (
            Antidote,
            Armor,
            Key,
            Potion,
            RewindScroll,
            Torch,
            Weapon,
        )

        parsers = {
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
        entidades = []
        for item in data.get("entidades", []):
            parser = parsers.get(item.get("clase", ""))
            if parser is None:
                raise KeyError(f"clase desconocida: {item.get('clase')}")
            entidades.append(parser(item))
        return cls(entidades=entidades)

@dataclass
class CatalogVersion:
    version: str

    @classmethod
    def from_dict(cls, data: dict) -> "CatalogVersion":
        return cls(
            version=data["version"],
        )