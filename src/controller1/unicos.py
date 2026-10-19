"""Deduplicación ordenada sin ``dict`` ni ``set`` (restricción §7).

Los lotes de ids que viajan al API son pequeños (fichas en uso, lote de
catálogo), así que una lista de vistos con búsqueda lineal alcanza y deja la
restricción "no dict como tabla de búsqueda" sin letra chica.
"""


def unicos(secuencia) -> list:
    """Primera aparición de cada elemento, preservando el orden de entrada."""
    vistos = []
    for x in secuencia:
        if x not in vistos:
            vistos.append(x)
    return vistos
