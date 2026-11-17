"""FIFO propia sobre arreglo dinámico y cursor de lectura."""


class ColaFIFO:
    def __init__(self):
        self._datos = []
        self._inicio = 0

    def __len__(self):
        return len(self._datos) - self._inicio

    def vacia(self):
        return self._inicio >= len(self._datos)

    def agregar(self, valor):
        self._datos.append(valor)

    def sacar(self):
        if self.vacia():
            raise IndexError("sacar de cola vacía")
        valor = self._datos[self._inicio]
        self._inicio += 1
        # Compactar de manera amortizada, sin mover el frente en cada extracción.
        if self._inicio >= 64 and self._inicio * 2 >= len(self._datos):
            self._datos = self._datos[self._inicio:]
            self._inicio = 0
        return valor
