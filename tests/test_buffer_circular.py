"""C2: buffer circular de mensajes (§4.8 doc oficial)."""

import pytest

from src.controller2.buffer_circular import BufferCircular


def test_rota_conservando_orden_cronologico():
    b = BufferCircular(3)
    for i in range(5):
        b.agregar(i)
    assert len(b) == 3
    assert b.ultimos() == [2, 3, 4]
    assert b.ultimos(2) == [3, 4]
    assert list(b) == [2, 3, 4]


def test_ultimos_pide_mas_de_lo_que_hay():
    b = BufferCircular(5)
    b.agregar("a")
    b.agregar("b")
    assert b.ultimos(20) == ["a", "b"]
    assert b.ultimos(0) == []


def test_memoria_constante_sin_copias():
    """Insertar 100 veces no reasigna ni agranda el arreglo interno."""
    b = BufferCircular(20)
    arreglo = b._datos
    for i in range(100):
        b.agregar(i)
    assert b._datos is arreglo
    assert len(b._datos) == 20
    assert b.ultimos() == list(range(80, 100))


def test_limpiar():
    b = BufferCircular(4)
    for i in range(6):
        b.agregar(i)
    b.limpiar()
    assert len(b) == 0 and b.ultimos() == []
    b.agregar("x")
    assert b.ultimos() == ["x"]


def test_capacidad_invalida():
    with pytest.raises(ValueError):
        BufferCircular(0)
