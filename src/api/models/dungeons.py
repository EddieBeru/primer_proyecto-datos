from dataclasses import dataclass, field

@dataclass
class PlayerInitial:
    vida_max: int  # > 0
    ataque: int
    defensa: int
    velocidad: int  # > 0

@dataclass
class DungeonGeneral:
    id: str
    version: str
    salas_total: int
    paginas: int
    salas_por_pagina: int
    sala_inicial: int
    sala_salida: int
    llave_salida: str
    presupuesto_solicitudes: int
    inventario_max: int
    jugador: PlayerInitial

@dataclass
class DungeonSummary:
    id: str
    nombre: str
    salas: int
    dificultad: int

@dataclass
class DungeonVersion:
    id: str
    version: str

@dataclass
class CriptasResponse:
    criptas: list[DungeonSummary] = field(default_factory=list)
