"""Segundo algoritmo de ordenamiento (§4.9): inserción.

Mergesort = estable O(n log n), bueno general y comparaciones costosas.
Inserción = O(n) casi-ordenado, mejor en n pequeño. Sin sort/sorted.
"""


def insertsort(lista, clave=lambda x: x):
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


def _casi_ordenado(items, clave, muestra: int = 16) -> bool:
    n = min(len(items), muestra)
    if n < 2:
        return True
    malas = 0
    for i in range(1, n):
        if clave(items[i]) < clave(items[i - 1]):
            malas += 1
    return malas <= max(1, n // 8)


def orden_auto(lista, clave=lambda x: x, algoritmo_grande=None, algoritmo_chico=None):
    """Elige automáticamente por propiedades medibles (§4.9).

    n <= 32 o casi-ordenado -> inserción; resto -> mergesort (inyectados).
    """
    from src.controller1.mergesort import mergesort
    grande = algoritmo_grande or mergesort
    chico = algoritmo_chico or insertsort
    items = list(lista)
    if len(items) <= 32 or _casi_ordenado(items, clave):
        return chico(items, clave)
    return grande(items, clave)


def vista_ordenada(ids: list, catalogo: dict, criterio: str = "nombre") -> list:
    """Vista ordenada del inventario sin mutar el orden real (§4.5)."""
    crit = (criterio or "nombre").lower()
    if crit == "peso":
        clave = lambda i: (getattr(catalogo.get(i), "peso", 0) or 0, str(i))
    elif crit == "valor":
        clave = lambda i: (getattr(catalogo.get(i), "valor", 0) or 0, str(i))
    else:
        clave = lambda i: (str(getattr(catalogo.get(i), "nombre", i)), str(i))
    return orden_auto(list(ids), clave)
