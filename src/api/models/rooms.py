from dataclasses import dataclass, field
from typing import Optional, Literal

@dataclass
class Exit:
    sala: int
    cerrada: Optional[bool] = None
    llave: Optional[str] = None
    cierre_automatico: Optional[int] = None  # > 0


@dataclass
class Room:
    id: int
    nombre: str
    # claves permitidas: "N", "S", "E", "O"
    salidas: dict[Literal["N", "S", "E", "O"], Exit] = field(default_factory=dict)


@dataclass
class SkeletonPage:
    pagina: int
    total_paginas: int
    salas: list[Room] = field(default_factory=list)