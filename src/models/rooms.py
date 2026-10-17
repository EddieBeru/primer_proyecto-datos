from dataclasses import dataclass, field
from typing import Optional, Literal

@dataclass
class Exit:
    sala: int
    cerrada: Optional[bool] = None
    llave: Optional[str] = None
    cierre_automatico: Optional[int] = None  # > 0

    @classmethod
    def from_dict(cls, data: dict) -> "Exit":
        return cls(
            sala=data["sala"],
            cerrada=data.get("cerrada"),
            llave=data.get("llave"),
            cierre_automatico=data.get("cierre_automatico"),
        )

@dataclass
class Room:
    id: int
    nombre: str
    # claves permitidas: "N", "S", "E", "O"
    salidas: dict[Literal["N", "S", "E", "O"], Exit] = field(default_factory=dict)
    # Sala a oscuras (mejoras 2026-10): la API puede traer "oscura"/"oscuridad".
    oscura: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "Room":
        salidas = {
            direccion: Exit.from_dict(salida)
            for direccion, salida in data.get("salidas", {}).items()
        }
        return cls(
            id=data["id"],
            nombre=data["nombre"],
            salidas=salidas,
            oscura=bool(data.get("oscura", data.get("oscuridad", False))),
        )

@dataclass
class SkeletonPage:
    pagina: int
    total_paginas: int
    salas: list[Room] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "SkeletonPage":
        return cls(
            pagina=data["pagina"],
            total_paginas=data["total_paginas"],
            salas=[Room.from_dict(item) for item in data.get("salas", [])],
        )