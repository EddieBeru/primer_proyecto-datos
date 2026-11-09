"""Metadatos inmutables compartidos; sin contenido ni estado vivo remoto."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Direccion = Literal["N", "S", "E", "O"]
Extremo = tuple[int, str]
DIRECCIONES: tuple[Direccion, ...] = ("N", "S", "E", "O")


def _validar_id(valor: int) -> None:
    if type(valor) is not int:
        raise TypeError("ID debe ser entero, sin conversión implícita")


def _validar_extremo(extremo: Extremo) -> None:
    if type(extremo) is not tuple or len(extremo) != 2:
        raise TypeError("extremo debe ser una tupla (sala_id, dirección)")
    _validar_id(extremo[0])
    if type(extremo[1]) is not str or extremo[1] not in DIRECCIONES:
        raise ValueError("dirección de extremo debe ser N, S, E u O")


@dataclass(frozen=True, slots=True)
class DatosSalida:
    direccion: Direccion
    destino: int
    costo: int
    puerta_id: Extremo

    def __post_init__(self) -> None:
        if type(self.direccion) is not str or self.direccion not in DIRECCIONES:
            raise ValueError("dirección debe ser N, S, E u O")
        _validar_id(self.destino)
        if type(self.costo) is not int:
            raise TypeError("costo debe ser entero")
        if self.costo < 1:
            raise ValueError("costo debe ser positivo")
        _validar_extremo(self.puerta_id)


@dataclass(frozen=True, slots=True)
class DatosSala:
    id: int
    nombre: str
    salidas: tuple[DatosSalida, ...]

    def __post_init__(self) -> None:
        _validar_id(self.id)
        if type(self.nombre) is not str:
            raise TypeError("nombre debe ser texto")
        if type(self.salidas) is not tuple:
            raise TypeError("salidas debe ser una tupla inmutable")
        if len(self.salidas) > 4:
            raise ValueError("una sala admite como máximo cuatro salidas")
        vistas = []
        for salida in self.salidas:
            if not isinstance(salida, DatosSalida):
                raise TypeError("salidas debe contener DatosSalida")
            if salida.direccion in vistas:
                raise ValueError("dirección de salida duplicada")
            vistas.append(salida.direccion)


def preparar_metadatos(salas):
    """Proyectar un plano una vez, unificando solo recíprocas opuestas declaradas."""
    from src.estructuras.tabla_indice import TablaIndice
    originales = TablaIndice()
    resultado = TablaIndice()
    for sala in salas:
        if sala.id in originales:
            raise ValueError("ID de sala duplicado")
        originales[sala.id] = sala
    opuestas = ("S", "N", "O", "E")
    for sala in originales.valores():
        salidas = []
        for direccion, salida in sala.salidas.items():
            if direccion not in DIRECCIONES or salida.sala not in originales:
                raise ValueError("dirección o destino de salida inválido")
            extremo = (sala.id, direccion)
            opuesta = opuestas[DIRECCIONES.index(direccion)]
            inversa = originales[salida.sala].salidas.get(opuesta)
            otro = (salida.sala, opuesta)
            if inversa is not None and inversa.sala == sala.id and otro < extremo:
                extremo = otro
            salidas.append(DatosSalida(direccion, salida.sala, getattr(salida, "costo", 100), extremo))
        # Orden estable por dirección, con grado acotado a cuatro.
        orden = tuple(s for d in DIRECCIONES for s in salidas if s.direccion == d)
        resultado[sala.id] = DatosSala(sala.id, sala.nombre, orden)
    return resultado


@dataclass(frozen=True, slots=True)
class MapaDTO:
    salas: tuple[dict, ...]
    revision: int
