"""DTO inmutables de la verificación previa de resolubilidad."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UbicacionLlave:
    id: str
    sala: int
    enemigo: str | None = None

    def __post_init__(self):
        if type(self.id) is not str or not self.id:
            raise ValueError("id de llave inválido")
        if type(self.sala) is not int:
            raise TypeError("sala de ubicación debe ser entera")
        if self.enemigo is not None and type(self.enemigo) is not str:
            raise TypeError("enemigo debe ser texto o None")


@dataclass(frozen=True, slots=True)
class UbicacionesLlaves:
    cripta_id: str
    version_cripta: str
    completa: bool
    llaves: tuple[UbicacionLlave, ...]

    def __post_init__(self):
        if type(self.cripta_id) is not str or type(self.version_cripta) is not str:
            raise TypeError("cripta y versión deben ser texto")
        if type(self.completa) is not bool:
            raise TypeError("completa debe ser booleano")
        if type(self.llaves) is not tuple or any(
                not isinstance(x, UbicacionLlave) for x in self.llaves):
            raise TypeError("llaves debe ser una tupla de UbicacionLlave")

    @classmethod
    def desde_dict(cls, dato):
        if type(dato) is not dict or type(dato.get("llaves")) is not list:
            raise ValueError("respuesta de ubicaciones inválida")
        if "formato" in dato and dato["formato"] != 1:
            raise ValueError("formato de ubicaciones no compatible")
        llaves = []
        for item in dato["llaves"]:
            if type(item) is not dict or type(item.get("id")) is not str:
                raise ValueError("ubicación de llave inválida")
            if type(item.get("sala")) is not int:
                raise ValueError("sala de ubicación inválida")
            enemigo = item.get("enemigo")
            if enemigo is not None and type(enemigo) is not str:
                raise ValueError("enemigo de ubicación inválido")
            llaves.append(UbicacionLlave(item["id"], item["sala"], enemigo))
        return cls(dato.get("cripta_id"), dato.get("version_cripta"),
                   dato.get("completa"), tuple(llaves))


@dataclass(frozen=True, slots=True)
class ResultadoResolubilidad:
    cripta_id: str
    version_cripta: str
    estado: str
    motivo: str = ""
    orden_llaves: tuple = ()
    llaves_no_obtenibles: tuple = ()
    frontera: tuple = ()
    ubicaciones: tuple = ()
    ciclo: tuple = ()
    alternativas_bloqueadas: tuple = ()
    contadores: tuple = ()
    tiempos_ns: tuple = ()

    def __post_init__(self):
        if self.estado not in ("resoluble", "no_resoluble", "incompleta"):
            raise ValueError("estado de resolubilidad inválido")
        for nombre in ("orden_llaves", "llaves_no_obtenibles", "frontera",
                       "ubicaciones", "ciclo", "alternativas_bloqueadas", "contadores"):
            if type(getattr(self, nombre)) is not tuple:
                raise TypeError(f"{nombre} debe ser inmutable")
        if type(self.tiempos_ns) is not tuple:
            raise TypeError("tiempos_ns debe ser inmutable")
