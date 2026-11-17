"""Cálculo de rutas óptimas y decisiones del enemigo cazador (001).

Restricción de Integridad Algorítmica:
Está TERMINANTEMENTE PROHIBIDO el uso de heapq, deque y set (ni como estructura auxiliar).
Todas las operaciones de cola de prioridad y tablas indexadas emplean exclusivamente
MonticuloMinimo y TablaIndice de src/estructuras/.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.controller2.modelo import EstadoPartida, SalidaViva
from src.estructuras.monticulo_minimo import MonticuloMinimo
from src.estructuras.tabla_indice import TablaIndice


@dataclass(slots=True)
class RutaCazador:
    """Caché transitoria de ruta para un enemigo cazador."""

    cazador_id: str
    sala_cazador: int
    sala_jugador: int
    puertas_version: int
    costo_total: int
    siguiente_sala: int | None
    pasos: list[int] = field(default_factory=list)

    def es_valida(self, estado: EstadoPartida, sala_actual_cazador: int) -> bool:
        """Verifica si la ruta almacenada sigue siendo válida sin cambios de contexto."""
        return (
            self.sala_jugador == estado.sala_actual
            and self.puertas_version == getattr(estado, "puertas_version", 0)
            and self.sala_cazador == sala_actual_cazador
            and self.siguiente_sala is not None
        )


def _obtener_salidas_sala(estado: EstadoPartida, sala_id: int, proveedor: Any = None):
    """Obtiene las salidas de una sala desde el estado o proveedor sin restricciones de niebla."""
    sala = estado.salas.get(sala_id)
    if sala is not None:
        return list(sala.salidas.values())
    if proveedor is not None and hasattr(proveedor, "datos_sala"):
        datos = proveedor.datos_sala(sala_id)
        salidas = []
        for salida in datos.salidas:
            # El extremo canónico conserva la puerta efectiva aunque la otra
            # sala aún no tenga contenido. Nunca usar niebla como estado vivo.
            extremo, direccion = salida.puerta_id
            viva = estado.salas.get(extremo)
            puerta = viva.salidas.get(direccion) if viva is not None else None
            cerrada = puerta.cerrada if puerta is not None else salida.cerrada_inicial
            salidas.append(SalidaViva(salida.direccion, salida.destino,
                                     cerrada=cerrada, llave=salida.llave,
                                     costo=salida.costo))
        return salidas
    return []


def distancias_desde_destino(
    estado: EstadoPartida,
    destino: int,
    rango_max: int | None = None,
    proveedor: Any = None,
) -> TablaIndice[int]:
    """Calcula distancias mínimas desde el destino hacia todas las salas dentro de rango_max.

    Utiliza búsqueda de Dijkstra acotada por rango_max con MonticuloMinimo y TablaIndice.
    Dada la simetría de costos de salida (FR-CAZ-01), dist(v, destino) == dist(destino, v).
    """
    distancias: TablaIndice[int] = TablaIndice()
    if destino not in estado.salas and (proveedor is None or not hasattr(proveedor, "datos_sala")):
        return distancias

    distancias[destino] = 0
    pq: MonticuloMinimo[int] = MonticuloMinimo()
    pq.insertar(0, destino)

    while len(pq) > 0:
        # Extraer sala con menor distancia acumulada
        actual = pq.extraer()
        d_actual = distancias[actual]

        salidas = _obtener_salidas_sala(estado, actual, proveedor)
        for salida in salidas:
            # Salidas cerradas no son transitables
            if getattr(salida, "cerrada", False):
                continue

            destino_vecino = getattr(salida, "destino", None)
            if destino_vecino is None:
                destino_vecino = getattr(salida, "sala", None)
            if destino_vecino is None:
                continue

            costo_salida = int(getattr(salida, "costo", 100))
            d_tentativa = d_actual + costo_salida

            # Poda por rango (FR-CAZ-14): no explorar más allá de rango_max
            if rango_max is not None and d_tentativa > rango_max:
                continue

            if destino_vecino not in distancias or d_tentativa < distancias[destino_vecino]:
                distancias[destino_vecino] = d_tentativa
                pq.insertar(d_tentativa, destino_vecino)

    return distancias


def dijkstra_acotado(
    estado: EstadoPartida,
    origen: int,
    destino: int,
    rango_max: int | None = None,
    distancias_destino: TablaIndice[int] | None = None,
    proveedor: Any = None,
) -> tuple[int | None, int | None]:
    """Calcula la distancia mínima d y la siguiente sala hacia destino dentro de rango_max.

    Retorna:
        (d, siguiente_sala): donde siguiente_sala es la vecina elegida por desempate de menor id.
        (None, None): si no hay camino viable o si d > rango_max.
    """
    if origen == destino:
        return 0, None

    sala_origen = estado.salas.get(origen)
    if sala_origen is None:
        return None, None

    if distancias_destino is None:
        return dijkstra_individual(estado, origen, destino, rango_max, proveedor)

    mejor_d: int | None = None
    vecinas_candidatas: list[int] = []

    for salida in sala_origen.salidas.values():
        if salida.cerrada:
            continue
        v = salida.destino
        costo_paso = int(getattr(salida, "costo", 100))

        if v == destino:
            d_v = costo_paso
        elif v in distancias_destino:
            d_v = costo_paso + distancias_destino[v]
        else:
            continue

        if rango_max is not None and d_v > rango_max:
            continue

        if mejor_d is None or d_v < mejor_d:
            mejor_d = d_v
            vecinas_candidatas = [v]
        elif d_v == mejor_d:
            vecinas_candidatas.append(v)

    if mejor_d is None:
        return None, None

    # Desempate estricto por menor id numérico entero (FR-CAZ-09)
    # Sin usar set: se busca el mínimo de la lista de candidatas
    elegida = vecinas_candidatas[0]
    for c in vecinas_candidatas[1:]:
        if c < elegida:
            elegida = c

    return mejor_d, elegida


def dijkstra_individual(
    estado: EstadoPartida,
    origen: int,
    destino: int,
    rango_max: int | None = None,
    proveedor: Any = None,
) -> tuple[int | None, int | None]:
    """Búsqueda de ruta de costo mínimo acotada por rango desde origen hacia destino.

    Explora salas partiendo de origen y se detiene si la distancia tentativa excede rango_max.
    Resuelve el desempate por menor id de sala vecina (FR-CAZ-09).
    No utiliza heapq, deque ni set.
    """
    if origen == destino:
        return 0, None
    sala_origen = estado.salas.get(origen)
    if sala_origen is None:
        return None, None

    etiquetas = TablaIndice()
    pendientes = MonticuloMinimo()
    etiquetas[origen] = (0, origen)
    pendientes.insertar((0, origen, origen), (origen, 0, origen))
    while pendientes:
        actual, costo, primero = pendientes.extraer()
        if etiquetas.obtener(actual) != (costo, primero):
            continue
        if actual == destino:
            return costo, primero
        for salida in _obtener_salidas_sala(estado, actual, proveedor):
            if getattr(salida, "cerrada", False):
                continue
            vecino = getattr(salida, "destino", getattr(salida, "sala", None))
            if vecino is None:
                continue
            nuevo_costo = costo + salida.costo
            if rango_max is not None and nuevo_costo > rango_max:
                continue
            nuevo_primero = vecino if actual == origen else primero
            nueva = (nuevo_costo, nuevo_primero)
            previa = etiquetas.obtener(vecino)
            if previa is None or nueva < previa:
                etiquetas[vecino] = nueva
                pendientes.insertar((nuevo_costo, nuevo_primero, vecino),
                                     (vecino, nuevo_costo, nuevo_primero))
    return None, None


class CampoCazadores:
    """Distancias compartidas con arcos inversos explícitos, incluso dirigidos."""

    def __init__(self, estado, proveedor):
        self.estado, self.proveedor = estado, proveedor
        self._entradas = TablaIndice()
        self._cantidad = -1
        self._contexto = None
        self._distancias = None

    def entradas(self, destino):
        if hasattr(self.proveedor, "entradas_sala"):
            return self.proveedor.entradas_sala(destino)
        # Adaptador técnico sin proveedor neutral: topología de salas vivas.
        if self._cantidad != len(self.estado.salas):
            self._entradas = TablaIndice()
            for sala in self.estado.salas.values():
                for direccion, salida in sala.salidas.items():
                    entradas = self._entradas.obtener(salida.destino)
                    if entradas is None:
                        entradas = []
                        self._entradas[salida.destino] = entradas
                    entradas.append((sala.id, direccion))
            self._cantidad = len(self.estado.salas)
        return self._entradas.obtener(destino, ())

    def obtener(self, rango):
        contexto = (self.estado.sala_actual, self.estado.puertas_version, len(self.estado.salas))
        if self._contexto == contexto and self._distancias is not None and self._rango >= rango:
            return self._distancias
        distancias = TablaIndice()
        destino = self.estado.sala_actual
        distancias[destino] = 0
        pendientes = MonticuloMinimo()
        pendientes.insertar(0, (destino, 0))
        while pendientes:
            actual, costo = pendientes.extraer()
            if distancias.obtener(actual) != costo:
                continue
            for origen, direccion in self.entradas(actual):
                salida = next((s for s in _obtener_salidas_sala(self.estado, origen, self.proveedor)
                               if s.direccion == direccion), None)
                if salida is None or salida.cerrada:
                    continue
                nuevo = costo + salida.costo
                if nuevo > rango:
                    continue
                previo = distancias.obtener(origen)
                if previo is None or nuevo < previo:
                    distancias[origen] = nuevo
                    pendientes.insertar(nuevo, (origen, nuevo))
        self._contexto, self._rango, self._distancias = contexto, rango, distancias
        return distancias
