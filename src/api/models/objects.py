from dataclasses import dataclass, field
from typing import Optional, Union

@dataclass
class Item:
    id: str
    nombre: str
    peso: int
    valor: int

@dataclass
class Antidote(Item):
    clase: str = field(default="antidoto", init=False)


@dataclass
class Armor(Item):
    defensa_bonus: int
    clase: str = field(default="armadura", init=False)

@dataclass
class Weapon(Item):
    ataque_bonus: int
    clase: str = field(default="arma", init=False)


@dataclass
class Potion(Item):
    cura: Optional[int] = None
    modificador_velocidad: Optional[int] = None
    duracion: Optional[int] = None
    clase: str = field(default="pocion", init=False)


@dataclass
class Key(Item):
    abre: Optional[Union[str, int]] = None
    clase: str = field(default="llave", init=False)


@dataclass
class Torch(Item):
    duracion: int
    clase: str = field(default="antorcha", init=False)


@dataclass
class RewindScroll(Item):
    clase: str = field(default="pergamino_retroceso", init=False)
