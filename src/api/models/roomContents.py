from dataclasses import dataclass, field
from typing import Optional

@dataclass
class EnemyPlacement:
    instancia: str
    tipo: str
    vida: Optional[int] = None

@dataclass
class TrapPlacement:
    instancia: str
    tipo: str

@dataclass
class RoomContentEntry:
    sala: int
    enemigos: list[EnemyPlacement] = field(default_factory=list)
    objetos: list[str] = field(default_factory=list)
    trampas: list[TrapPlacement] = field(default_factory=list)

@dataclass
class ContenidoResponse:
    contenido: list[RoomContentEntry] = field(default_factory=list)