from dataclasses import dataclass, field
from typing import Optional, Union

@dataclass
class Item:
    id: str
    nombre: str
    peso: int
    valor: int

    @classmethod
    def from_dict(cls, data: dict) -> "Item":
        return cls(
            id=data["id"],
            nombre=data["nombre"],
            peso=data["peso"],
            valor=data["valor"],
        )

@dataclass
class Antidote(Item):
    clase: str = field(default="antidoto", init=False)

    @classmethod
    def from_dict(cls, data: dict) -> "Antidote":
        return cls(
            id=data["id"],
            nombre=data["nombre"],
            peso=data["peso"],
            valor=data["valor"],
        )

@dataclass
class Armor(Item):
    defensa_bonus: int
    clase: str = field(default="armadura", init=False)

    @classmethod
    def from_dict(cls, data: dict) -> "Armor":
        return cls(
            id=data["id"],
            nombre=data["nombre"],
            peso=data["peso"],
            valor=data["valor"],
            defensa_bonus=data["defensa_bonus"],
        )

@dataclass
class Weapon(Item):
    ataque_bonus: int
    clase: str = field(default="arma", init=False)

    @classmethod
    def from_dict(cls, data: dict) -> "Weapon":
        return cls(
            id=data["id"],
            nombre=data["nombre"],
            peso=data["peso"],
            valor=data["valor"],
            ataque_bonus=data["ataque_bonus"],
        )

@dataclass
class Potion(Item):
    cura: Optional[int] = None
    modificador_velocidad: Optional[int] = None
    duracion: Optional[int] = None
    clase: str = field(default="pocion", init=False)

    @classmethod
    def from_dict(cls, data: dict) -> "Potion":
        return cls(
            id=data["id"],
            nombre=data["nombre"],
            peso=data["peso"],
            valor=data["valor"],
            cura=data.get("cura"),
            modificador_velocidad=data.get("modificador_velocidad"),
            duracion=data.get("duracion"),
        )

@dataclass
class Key(Item):
    abre: Optional[Union[str, int]] = None
    clase: str = field(default="llave", init=False)

    @classmethod
    def from_dict(cls, data: dict) -> "Key":
        return cls(
            id=data["id"],
            nombre=data["nombre"],
            peso=data["peso"],
            valor=data["valor"],
            abre=data.get("abre"),
        )

@dataclass
class Torch(Item):
    duracion: int
    clase: str = field(default="antorcha", init=False)

    @classmethod
    def from_dict(cls, data: dict) -> "Torch":
        return cls(
            id=data["id"],
            nombre=data["nombre"],
            peso=data["peso"],
            valor=data["valor"],
            duracion=data["duracion"],
        )

@dataclass
class RewindScroll(Item):
    clase: str = field(default="pergamino_retroceso", init=False)

    @classmethod
    def from_dict(cls, data: dict) -> "RewindScroll":
        return cls(
            id=data["id"],
            nombre=data["nombre"],
            peso=data["peso"],
            valor=data["valor"],
        )
