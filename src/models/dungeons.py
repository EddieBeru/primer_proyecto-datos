from dataclasses import dataclass, field

@dataclass
class PlayerInitial:
    vida_max: int  # > 0
    ataque: int
    defensa: int
    velocidad: int  # > 0

    @classmethod
    def from_dict(cls, data: dict) -> "PlayerInitial":
        return cls(
            vida_max=data["vida_max"],
            ataque=data["ataque"],
            defensa=data["defensa"],
            velocidad=data["velocidad"],
        )

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

    @classmethod
    def from_dict(cls, data: dict) -> "DungeonGeneral":
        return cls(
            id=data["id"],
            version=data["version"],
            salas_total=data["salas_total"],
            paginas=data["paginas"],
            salas_por_pagina=data["salas_por_pagina"],
            sala_inicial=data["sala_inicial"],
            sala_salida=data["sala_salida"],
            llave_salida=data["llave_salida"],
            presupuesto_solicitudes=data["presupuesto_solicitudes"],
            inventario_max=data["inventario_max"],
            jugador=PlayerInitial.from_dict(data["jugador"]),
        )

@dataclass
class DungeonSummary:
    id: str
    nombre: str
    salas: int
    dificultad: int

    @classmethod
    def from_dict(cls, data: dict) -> "DungeonSummary":
        return cls(
            id=data["id"],
            nombre=data["nombre"],
            salas=data["salas"],
            dificultad=data["dificultad"],
        )

@dataclass
class DungeonVersion:
    id: str
    version: str

    @classmethod
    def from_dict(cls, data: dict) -> "DungeonVersion":
        return cls(
            id=data["id"],
            version=data["version"],
        )

@dataclass
class CriptasResponse:
    criptas: list[DungeonSummary] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "CriptasResponse":
        return cls(
            criptas=[DungeonSummary.from_dict(item) for item in data.get("criptas", [])],
        )
