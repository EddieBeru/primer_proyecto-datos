"""Ordenamiento por inserción local de C2 (sin `sorted`, §4.9).

El motor no importa controller1 (regla de capas), así que mantiene su
propio algoritmo para listas pequeñas y casi ordenadas: agenda reconstruida,
padrón de enemigos de una sala, vecinas deterministas para el errante.
Recibe lista + clave y devuelve lista NUEVA ordenada (estable).
"""

from __future__ import annotations


def insercion(lista, clave=lambda x: x):
    items = list(lista)
    for i in range(1, len(items)):
        actual = items[i]
        kc = clave(actual)
        j = i - 1
        while j >= 0 and clave(items[j]) > kc:
            items[j + 1] = items[j]
            j -= 1
        items[j + 1] = actual
    return items
