"""Lista doblemente enlazada propia (C1-6, C2 la usa de ejemplo para inventario).

Nodos con anterior/siguiente. Frente = más reciente, cola = menos reciente.
Sin estructuras nativas como índice: solo enlaces.
"""


class Nodo:
    def __init__(self, clave, valor):
        self.clave = clave
        self.valor = valor
        self.anterior = None
        self.siguiente = None


class ListaDoble:
    def __init__(self):
        self.cabeza = None
        self.cola = None
        self._tam = 0

    def __len__(self):
        return self._tam

    def __iter__(self):
        actual = self.cabeza
        while actual is not None:
            yield actual
            actual = actual.siguiente

    def hacia_atras(self):
        actual = self.cola
        while actual is not None:
            yield actual
            actual = actual.anterior

    def agregar_frente(self, nodo):
        nodo.anterior = None
        nodo.siguiente = self.cabeza
        if self.cabeza is not None:
            self.cabeza.anterior = nodo
        self.cabeza = nodo
        if self.cola is None:
            self.cola = nodo
        self._tam += 1

    def quitar(self, nodo):
        if nodo.anterior is not None:
            nodo.anterior.siguiente = nodo.siguiente
        else:
            self.cabeza = nodo.siguiente
        if nodo.siguiente is not None:
            nodo.siguiente.anterior = nodo.anterior
        else:
            self.cola = nodo.anterior
        nodo.anterior = None
        nodo.siguiente = None
        self._tam -= 1

    def mover_frente(self, nodo):
        if nodo is self.cabeza:
            return
        self.quitar(nodo)
        self.agregar_frente(nodo)

    def sacar_cola(self):
        if self.cola is None:
            return None
        nodo = self.cola
        self.quitar(nodo)
        return nodo
