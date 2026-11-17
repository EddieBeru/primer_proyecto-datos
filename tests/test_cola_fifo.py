"""Contrato de la cola FIFO propia usada por recorridos incrementales."""

import pytest

from src.estructuras.cola_fifo import ColaFIFO


def test_vacia_y_fifo_con_crecimiento():
    cola = ColaFIFO()
    assert cola.vacia()
    with pytest.raises(IndexError):
        cola.sacar()
    for valor in range(1000):
        cola.agregar(valor)
    assert [cola.sacar() for _ in range(1000)] == list(range(1000))
    assert cola.vacia()


def test_extraccion_avanza_cursor_sin_desplazar_frente():
    cola = ColaFIFO()
    for valor in range(20):
        cola.agregar(valor)
    arreglo = cola._datos
    cola.sacar()
    assert cola._datos is arreglo
    assert cola._inicio == 1
