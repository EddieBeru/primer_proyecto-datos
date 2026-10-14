"""C1-11 Mergesort propio. Prohibido list.sort() y sorted() (restricción proyecto).

Lo usa C2 para ordenar inventario y puntajes. Recibe lista + criterio
(clave) y retorna lista NUEVA ordenada (estable), sin mutar la entrada.
"""


def mergesort(lista, clave=lambda x: x):
    items = list(lista)
    if len(items) < 2:
        return items
    medio = len(items) // 2
    izq = mergesort(items[:medio], clave)
    der = mergesort(items[medio:], clave)
    return _mezclar(izq, der, clave)


def _mezclar(izq, der, clave):
    salida = []
    i = j = 0
    while i < len(izq) and j < len(der):
        if clave(izq[i]) <= clave(der[j]):
            salida.append(izq[i])
            i += 1
        else:
            salida.append(der[j])
            j += 1
    salida.extend(izq[i:])
    salida.extend(der[j:])
    return salida
