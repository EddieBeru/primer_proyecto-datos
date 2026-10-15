"""Caché LRU del catálogo (C1-6, Flujo H).

Frente de la lista = más reciente; al llenarse se expulsa la cola.
Hit promueve al frente. Miss retorna None (C1-7 pide a red).
Versión del catálogo (endpoint 6): si cambia, se invalida todo.
Disco: pickle con (version, [(id, ficha)...] de más a menos reciente);
al cargar solo entran las `capacidad` primeras. Formato propio de C1.
"""

import pickle

from src.controller1.lista_doble import ListaDoble, Nodo
from src.controller1.tabla_hash import TablaHash


class CacheLRU:
    """LRU §4.4: tope configurable, fichas en uso no desalojables, persiste en disco."""

    def __init__(self, capacidad, version=None):
        if capacidad < 1:
            raise ValueError(f"capacidad debe ser >= 1, llegó {capacidad}")
        self.capacidad = capacidad
        self.version = version
        self._orden = ListaDoble()
        self._indice = TablaHash()
        self._fijas: set = set()  # ids en uso: fuera de la política de desalojo

    def __len__(self):
        return len(self._orden)

    def obtener(self, clave):
        nodo = self._indice.obtener(clave)
        if nodo is None:
            return None
        self._orden.mover_frente(nodo)
        return nodo.valor

    def guardar(self, clave, ficha):
        nodo = self._indice.obtener(clave)
        if nodo is not None:
            nodo.valor = ficha
            self._orden.mover_frente(nodo)
            return
        nuevo = Nodo(clave, ficha)
        self._orden.agregar_frente(nuevo)
        self._indice.poner(clave, nuevo)
        while len(self._orden) > self.capacidad:
            expulsado = self._elegir_victima()
            if expulsado is None:
                break  # todo fijado en uso: se conserva (documentado)
            self._orden.quitar(expulsado)
            self._indice.eliminar(expulsado.clave)

    def _elegir_victima(self):
        actual = self._orden.cola
        while actual is not None:
            if actual.clave not in self._fijas:
                return actual
            actual = actual.anterior
        return None

    def fijar_en_uso(self, claves) -> None:
        """Marca fichas referenciadas (vivas/suelo/actual) como no desalojables."""
        self._fijas = set(claves or [])

    def liberar(self, clave) -> None:
        self._fijas.discard(clave)

    def invalida_si_cambia(self, nueva_version):
        """True si la versión cambió (caché limpiada); False si sigue válida."""
        if nueva_version == self.version:
            return False
        self.version = nueva_version
        self._orden = ListaDoble()
        self._indice = TablaHash()
        return True

    def guardar_disco(self, ruta):
        pares = [(nodo.clave, nodo.valor) for nodo in self._orden]
        with open(ruta, "wb") as f:
            pickle.dump((self.version, pares), f)

    @classmethod
    def cargar_disco(cls, ruta, capacidad):
        with open(ruta, "rb") as f:
            version, pares = pickle.load(f)
        if not isinstance(pares, list):
            raise ValueError(f"caché dañada: {ruta}")
        cache = cls(capacidad, version)
        for clave, ficha in reversed(pares[:capacidad]):
            cache.guardar(clave, ficha)
        return cache
