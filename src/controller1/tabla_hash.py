"""Tabla hash propia con encadenamiento (C1-6).

Prohibido dict como índice principal: el índice es un arreglo de
cubetas; cada cubeta es una lista de Nodos (de lista_doble).
Solo guarda referencias a los nodos que viven en la ListaDoble del LRU.
"""

from src.controller1.lista_doble import Nodo


class TablaHash:
    def __init__(self, cubetas=53):
        if cubetas < 1:
            raise ValueError(f"cubetas debe ser >= 1, llegó {cubetas}")
        self._cubetas = [[] for _ in range(cubetas)]
        self._tam = 0

    def __len__(self):
        return self._tam

    def __contains__(self, clave):
        return self.obtener(clave) is not None

    def _indice(self, clave):
        h = 0
        for ch in str(clave):
            h = (h * 31 + ord(ch)) & 0xFFFFFFFF
        return h % len(self._cubetas)

    def poner(self, clave, nodo):
        cubeta = self._cubetas[self._indice(clave)]
        for i, actual in enumerate(cubeta):
            if actual.clave == clave:
                cubeta[i] = nodo
                return
        cubeta.append(nodo)
        self._tam += 1

    def obtener(self, clave):
        for actual in self._cubetas[self._indice(clave)]:
            if actual.clave == clave:
                return actual
        return None

    def eliminar(self, clave):
        cubeta = self._cubetas[self._indice(clave)]
        for i, actual in enumerate(cubeta):
            if actual.clave == clave:
                del cubeta[i]
                self._tam -= 1
                return True
        return False
