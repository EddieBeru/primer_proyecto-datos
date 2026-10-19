"""Buffer circular de mensajes (§4.8 doc oficial).

La fachada muestra "los últimos N mensajes"; con una lista normal, cada
inserción con la lista llena copia 20 posiciones (O(N) por mensaje). Este
buffer tiene capacidad fija y nunca desplaza elementos:

- ``agregar``: O(1), sobrescribe el más viejo cuando está lleno.
- ``ultimos(k)``: O(k) y solo cuando alguien pide la foto.
- memoria acotada desde el minuto cero (no crece ni se recorta).
"""


class BufferCircular:
    """Cola FIFO de capacidad fija. Iterar recorre de más viejo a más nuevo."""

    def __init__(self, capacidad: int = 20) -> None:
        if capacidad < 1:
            raise ValueError(f"capacidad debe ser >= 1, llegó {capacidad}")
        self.capacidad = capacidad
        self._datos: list = [None] * capacidad
        self._inicio = 0
        self._n = 0

    def __len__(self) -> int:
        return self._n

    def agregar(self, item) -> None:
        if self._n == self.capacidad:
            # Lleno: el más viejo (inicio) se sobrescribe y el inicio avanza.
            self._datos[self._inicio] = item
            self._inicio = (self._inicio + 1) % self.capacidad
            return
        self._datos[(self._inicio + self._n) % self.capacidad] = item
        self._n += 1

    def ultimos(self, k: int | None = None) -> list:
        """Copia de los últimos k (todos si k es None), en orden cronológico."""
        n = self._n if k is None else min(int(k), self._n)
        return [self._datos[(self._inicio + self._n - n + i) % self.capacidad]
                for i in range(n)]

    def limpiar(self) -> None:
        self._datos = [None] * self.capacidad
        self._inicio = 0
        self._n = 0

    def __iter__(self):
        for i in range(self._n):
            yield self._datos[(self._inicio + i) % self.capacidad]
