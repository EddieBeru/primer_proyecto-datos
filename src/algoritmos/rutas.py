"""Dijkstra sobre adyacencia inyectada; no conoce proveedor ni estado vivo."""

from dataclasses import dataclass

from src.estructuras.monticulo_minimo import MonticuloMinimo
from src.estructuras.tabla_indice import TablaIndice


@dataclass(frozen=True, slots=True)
class ResultadoRuta:
    alcanzable: bool
    costo_total: int | None = None
    primer_vecino: int | None = None
    direccion: str | None = None


def siguiente_paso(origen, destino, adyacentes):
    if origen == destino:
        return ResultadoRuta(True, 0)
    etiquetas = TablaIndice()
    pendientes = MonticuloMinimo()
    etiquetas[origen] = (0, origen, None)
    pendientes.insertar((0, origen, origen), (origen, 0, origen, None))
    while pendientes:
        actual, costo, primero, direccion = pendientes.extraer()
        if etiquetas.obtener(actual) != (costo, primero, direccion):
            continue
        if actual == destino:
            return ResultadoRuta(True, costo, primero, direccion)
        for salida in adyacentes(actual):
            if type(salida.costo) is not int or salida.costo < 1:
                raise ValueError("Dijkstra exige costos enteros positivos")
            vecino = salida.destino
            primero_nuevo = vecino if actual == origen else primero
            direccion_nueva = salida.direccion if actual == origen else direccion
            nuevo = (costo + salida.costo, primero_nuevo, direccion_nueva)
            previo = etiquetas.obtener(vecino)
            # N,S,E,O ya es el orden de adyacencia para los arcos paralelos.
            if previo is None or nuevo[:2] < previo[:2]:
                etiquetas[vecino] = nuevo
                pendientes.insertar((nuevo[0], nuevo[1], vecino), (vecino, *nuevo))
    return ResultadoRuta(False)
