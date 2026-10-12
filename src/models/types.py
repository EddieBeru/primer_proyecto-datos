from typing import TypeAlias, Union

from models.catalog import Enemy, Trap
from models.objects import Antidote, Armor, Key, Potion, RewindScroll, Torch, Weapon

# Almacena la lista de todas las clases de entidaddes. 
Entidad: TypeAlias = Union[
    Enemy, Weapon, Armor, Potion, Antidote, Key, Torch, RewindScroll, Trap
]