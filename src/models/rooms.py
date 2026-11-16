from dataclasses import dataclass, field
from typing import Optional, Literal

@dataclass
class Exit:
    sala: int
    cerrada: Optional[bool] = None
    llave: Optional[str] = None
    cierre_automatico: Optional[int] = None  # > 0
    costo: int = 100

    def __post_init__(self) -> None:
        if not isinstance(self.costo, int) or isinstance(self.costo, bool) or self.costo < 1:
            raise ValueError(f"costo debe ser un entero >= 1, recibido: {self.costo}")

    @classmethod
    def from_dict(cls, data: dict) -> "Exit":
        costo = data.get("costo", 100)
        if costo is None:
            costo = 100
        return cls(
            sala=data["sala"],
            cerrada=data.get("cerrada"),
            llave=data.get("llave"),
            cierre_automatico=data.get("cierre_automatico"),
            costo=costo,
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