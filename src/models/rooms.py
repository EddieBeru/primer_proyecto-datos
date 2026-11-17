from dataclasses import dataclass, field
from typing import Optional, Literal

@dataclass
class Exit:
    sala: int
    cerrada: Optional[bool] = None
    llave: Optional[str] = None
    cierre_automatico: Optional[int] = None  # > 0
    costo: int = 100
    cerrada_inicial: Optional[bool] = None

    def __post_init__(self):
        if type(self.costo) is not int:
            raise TypeError("costo de salida debe ser entero")
        if self.costo < 1:
            raise ValueError("costo de salida debe ser positivo")
        if self.llave is not None and type(self.llave) is not str:
            raise TypeError("llave de salida debe ser texto o None")
        if self.cerrada_inicial is None:
            self.cerrada_inicial = bool(self.cerrada)
        if type(self.cerrada_inicial) is not bool:
            raise TypeError("cerrada_inicial debe ser booleano")

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
            costo=data.get("costo", 100),
            cerrada_inicial=data.get("cerrada", False),
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
