"""C1-11: mergesort ordena, es estable, no muta, sin sort()/sorted()."""

import random
import time

from src.adapters.mergesort import mergesort


def test_vacia_y_uno():
    assert mergesort([]) == []
    assert mergesort([5]) == [5]


def test_ordenada_e_inversa():
    assert mergesort([1, 2, 3]) == [1, 2, 3]
    assert mergesort([3, 2, 1]) == [1, 2, 3]


def test_repetidos():
    assert mergesort([3, 1, 2, 1, 3]) == [1, 1, 2, 3, 3]


def test_no_muta_entrada():
    entrada = [3, 1, 2]
    mergesort(entrada)
    assert entrada == [3, 1, 2]


def test_estable_con_clave():
    items = [("b", 1), ("a", 1), ("c", 0)]
    assert mergesort(items, clave=lambda t: t[1]) == [("c", 0), ("b", 1), ("a", 1)]


def test_clave_objetos():
    class Obj:
        def __init__(self, nombre, valor):
            self.nombre = nombre
            self.valor = valor

    mochila = [Obj("espada", 50), Obj("pan", 5), Obj("escudo", 30)]
    orden = mergesort(mochila, clave=lambda o: o.valor)
    assert [o.nombre for o in orden] == ["pan", "escudo", "espada"]


def test_oraculo_aleatorio():
    rng = random.Random(42)
    datos = [rng.randint(0, 100) for _ in range(300)]
    assert mergesort(datos) == sorted(datos)


def test_sin_sort_prohibido():
    dentro_doc = False
    for linea in open("src/adapters/mergesort.py"):
        s = linea.strip()
        if s.startswith('"""'):
            dentro_doc = not dentro_doc
            continue
        if dentro_doc or not s or s.startswith("#"):
            continue
        assert ".sort(" not in s and "sorted(" not in s, f"uso prohibido: {s}"


def test_tiempos_crecientes():
    # Humo para --bench: registra tiempos, no exige cotas.
    rng = random.Random(7)
    for n in (100, 1000, 5000):
        datos = [rng.randint(0, n) for _ in range(n)]
        t0 = time.perf_counter()
        mergesort(datos)
        dt = time.perf_counter() - t0
        print(f"\nmergesort n={n}: {dt:.4f}s")
        assert dt < 10
