"""Índice hash propio con encadenamiento y crecimiento amortizado.

Claves enteras o extremos (ID de sala, dirección). El hash no depende de la
semilla de hash de Python. Cada expansión duplica las cubetas al superar 0,75
de carga; el espacio depende de la cantidad de claves, nunca de su máximo ID.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Iterator, TypeVar

Clave = int | str | tuple[int, str]
V = TypeVar("V")
_DIRECCIONES = ("N", "S", "E", "O")
_MASCARA = (1 << 64) - 1


def _hash_entero(valor: int) -> int:
    # Zigzag conserva signo; mezclar todos los bloques admite IDs arbitrarios.
    numero = valor * 2 if valor >= 0 else -valor * 2 - 1
    resultado = 0x9E3779B97F4A7C15
    while True:
        bloque = numero & _MASCARA
        resultado ^= bloque + 0x9E3779B97F4A7C15
        resultado = ((resultado ^ (resultado >> 30)) * 0xBF58476D1CE4E5B9) & _MASCARA
        resultado = ((resultado ^ (resultado >> 27)) * 0x94D049BB133111EB) & _MASCARA
        resultado ^= resultado >> 31
        numero >>= 64
        if numero == 0:
            return resultado


def _hash_clave(clave: Clave) -> int:
    if type(clave) is int:
        return _hash_entero(clave)
    if type(clave) is str:
        valor = 0xCBF29CE484222325
        for byte in clave.encode("utf-8"):
            valor ^= byte
            valor = (valor * 0x100000001B3) & _MASCARA
        return valor
    if type(clave) is not tuple or len(clave) != 2 or type(clave[0]) is not int:
        raise TypeError("clave debe ser entero o extremo (entero, dirección)")
    if type(clave[1]) is not str or clave[1] not in _DIRECCIONES:
        raise ValueError("dirección de extremo debe ser N, S, E u O")
    return _hash_entero(_hash_entero(clave[0]) * 4 + _DIRECCIONES.index(clave[1]))


@dataclass(slots=True)
class _Entrada(Generic[V]):
    clave: Clave
    valor: V
    hash: int
    siguiente: _Entrada[V] | None = None


class TablaIndice(Generic[V]):
    """Consulta esperada O(1); inserción esperada amortizada O(1).

    ``items`` recorre las cubetas y cadenas sin ordenar ni copiar registros.
    No modificar el índice mientras se itera sobre él.
    """

    def __init__(self, capacidad: int = 8) -> None:
        if type(capacidad) is not int or capacidad <= 0:
            raise ValueError("capacidad debe ser un entero positivo")
        tamano = 4
        while tamano < capacidad:
            tamano *= 2
        self._cubetas: list[_Entrada[V] | None] = [None] * tamano
        self._cantidad = 0
        self.salas_en_orden = ()

    @property
    def capacidad(self) -> int:
        return len(self._cubetas)

    def __len__(self) -> int:
        return self._cantidad

    def _indice(self, clave: Clave) -> int:
        return _hash_clave(clave) & (self.capacidad - 1)

    def _buscar_hash(self, clave: Clave, hash_clave: int) -> _Entrada[V] | None:
        entrada = self._cubetas[hash_clave & (self.capacidad - 1)]
        while entrada is not None:
            if entrada.hash == hash_clave and entrada.clave == clave:
                return entrada
            entrada = entrada.siguiente
        return None

    def _buscar(self, clave: Clave) -> _Entrada[V] | None:
        return self._buscar_hash(clave, _hash_clave(clave))

    def __contains__(self, clave: Clave) -> bool:
        return self._buscar(clave) is not None

    def __getitem__(self, clave: Clave) -> V:
        entrada = self._buscar(clave)
        if entrada is None:
            raise KeyError(clave)
        return entrada.valor

    def obtener(self, clave: Clave, defecto=None):
        entrada = self._buscar(clave)
        return defecto if entrada is None else entrada.valor

    def __setitem__(self, clave: Clave, valor: V) -> None:
        hash_clave = _hash_clave(clave)
        entrada = self._buscar_hash(clave, hash_clave)
        if entrada is not None:
            entrada.valor = valor
            return
        if (self._cantidad + 1) * 4 > self.capacidad * 3:
            self._expandir()
        indice = hash_clave & (self.capacidad - 1)
        self._cubetas[indice] = _Entrada(clave, valor, hash_clave, self._cubetas[indice])
        self._cantidad += 1

    def insertar_si_ausente(self, clave: Clave, valor: V) -> tuple[V, bool]:
        """Inserta solo si falta; devuelve el valor vigente y si fue nuevo."""
        hash_clave = _hash_clave(clave)
        entrada = self._buscar_hash(clave, hash_clave)
        if entrada is not None:
            return entrada.valor, False
        if (self._cantidad + 1) * 4 > self.capacidad * 3:
            self._expandir()
        indice = hash_clave & (self.capacidad - 1)
        self._cubetas[indice] = _Entrada(clave, valor, hash_clave, self._cubetas[indice])
        self._cantidad += 1
        return valor, True

    def _expandir(self) -> None:
        anteriores = self._cubetas
        self._cubetas = [None] * (2 * len(anteriores))
        for entrada in anteriores:
            while entrada is not None:
                siguiente = entrada.siguiente
                indice = entrada.hash & (self.capacidad - 1)
                entrada.siguiente = self._cubetas[indice]
                self._cubetas[indice] = entrada
                entrada = siguiente

    def borrar(self, clave: Clave) -> bool:
        indice = self._indice(clave)
        entrada = self._cubetas[indice]
        anterior = None
        while entrada is not None:
            if entrada.clave == clave:
                if anterior is None:
                    self._cubetas[indice] = entrada.siguiente
                else:
                    anterior.siguiente = entrada.siguiente
                self._cantidad -= 1
                return True
            anterior, entrada = entrada, entrada.siguiente
        return False

    def __delitem__(self, clave: Clave) -> None:
        if not self.borrar(clave):
            raise KeyError(clave)

    def items(self) -> Iterator[tuple[Clave, V]]:
        for entrada in self._cubetas:
            while entrada is not None:
                yield entrada.clave, entrada.valor
                entrada = entrada.siguiente

    def __iter__(self) -> Iterator[Clave]:
        for clave, _ in self.items():
            yield clave

    def valores(self) -> Iterator[V]:
        for _, valor in self.items():
            yield valor
