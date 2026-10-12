from typing import TypeAlias, Union

from api.models.catalog import Enemy, Trap
from api.models.objects import Antidote, Armor, Key, Potion, RewindScroll, Torch, Weapon

Entidad: TypeAlias = Union[
    Enemy, Weapon, Armor, Potion, Antidote, Key, Torch, RewindScroll, Trap
]