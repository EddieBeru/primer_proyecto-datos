"""Heap propio: orden, empates estables y valores no comparables."""

import pytest

from src.estructuras.monticulo_minimo import MonticuloMinimo


def test_prioridad_total_y_empates_sin_comparar_valores():
    heap = MonticuloMinimo()
    primero, segundo = object(), object()
    heap.insertar((3, 0), "ultimo")
    heap.insertar((1, 2), primero)
    heap.insertar((1, 2), segundo)
    heap.insertar((1, 1), "inicio")
    assert len(heap) == 4
    assert heap.extraer() == "inicio"
    assert heap.extraer() is primero
    assert heap.extraer() is segundo
    assert heap.extraer() == "ultimo"
    assert len(heap) == 0 and not heap


def test_intercalar_insercion_y_extraccion():
    heap = MonticuloMinimo()
    for prioridad in (8, 2, 7, 1, 4, 3):
        heap.insertar(prioridad, prioridad)
    assert heap.extraer() == 1
    assert heap.extraer() == 2
    heap.insertar(0, "nuevo")
    assert heap.extraer() == "nuevo"
    assert [heap.extraer() for _ in range(4)] == [3, 4, 7, 8]


def test_vacio_y_reutilizacion():
    heap = MonticuloMinimo()
    with pytest.raises(IndexError):
        heap.extraer()
    heap.insertar(0, None)
    assert heap.extraer() is None
    with pytest.raises(IndexError):
        heap.extraer()
