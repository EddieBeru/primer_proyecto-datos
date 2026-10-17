from dataclasses import dataclass, field
from typing import Optional

@dataclass
class EnemyPlacement:
    instancia: str
    tipo: str
    vida: Optional[int] = None

    @classmethod
    def from_dict(cls, data: dict) -> "EnemyPlacement":
        return cls(
            instancia=data["instancia"],
            tipo=data["tipo"],
            vida=data.get("vida"),
        )

@dataclass
class TrapPlacement:
    instancia: str
    tipo: str

    @classmethod
    def from_dict(cls, data: dict) -> "TrapPlacement":
        return cls(
            instancia=data["instancia"],
            tipo=data["tipo"],
        )

@dataclass
class RoomContentEntry:
    sala: int
    enemigos: list[EnemyPlacement] = field(default_factory=list)
    objetos: list[str] = field(default_factory=list)
    trampas: list[TrapPlacement] = field(default_factory=list)
    # Mejoras 2026-10: la oscuridad también puede venir en el contenido.
    oscura: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "RoomContentEntry":
        return cls(
            sala=data["sala"],
            enemigos=[EnemyPlacement.from_dict(item) for item in data.get("enemigos", [])],
            objetos=list(data.get("objetos", [])),
            trampas=[TrapPlacement.from_dict(item) for item in data.get("trampas", [])],
            oscura=bool(data.get("oscura", data.get("oscuridad", False))),
        )

@dataclass
class ContenidoResponse:
    contenido: list[RoomContentEntry] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "ContenidoResponse":
        return cls(
            contenido=[RoomContentEntry.from_dict(item) for item in data.get("contenido", [])],
        )