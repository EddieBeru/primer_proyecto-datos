"""Validación e inmutabilidad de los DTO neutrales de metadatos."""

from dataclasses import FrozenInstanceError

import pytest

from src.models.conocimiento import DatosSala, DatosSalida


def test_datos_inmutables_con_ids_dispersos():
    salida = DatosSalida("N", 10**12, 7, (2, "N"))
    sala = DatosSala(2, "Entrada", (salida,))
    assert sala.salidas == (salida,) and sala.salidas[0].destino == 10**12
    with pytest.raises(FrozenInstanceError):
        sala.nombre = "otro"
    with pytest.raises(FrozenInstanceError):
        salida.costo = 1


@pytest.mark.parametrize("costo", [0, -1, True, "5", 1.5, None])
def test_costo_invalido_no_se_normaliza(costo):
    with pytest.raises((TypeError, ValueError)):
        DatosSalida("N", 5, costo, (2, "N"))


@pytest.mark.parametrize("direccion", ["n", "X", "", None])
def test_direccion_invalida(direccion):
    with pytest.raises((TypeError, ValueError)):
        DatosSalida(direccion, 5, 1, (2, "N"))


@pytest.mark.parametrize("extremo", [(2, "X"), (True, "N"), [2, "N"], (2,), None])
def test_extremo_invalido(extremo):
    with pytest.raises((TypeError, ValueError)):
        DatosSalida("N", 5, 1, extremo)


def test_sala_rechaza_colecciones_mutables_direcciones_duplicadas_y_mas_de_cuatro():
    salida = DatosSalida("N", 5, 1, (2, "N"))
    for salidas in ([salida], (salida, salida), (salida,) * 5, (object(),)):
        with pytest.raises((TypeError, ValueError)):
            DatosSala(2, "Sala", salidas)


@pytest.mark.parametrize("sala_id", [True, "2", 2.0])
def test_ids_enteros_estrictos(sala_id):
    with pytest.raises(TypeError):
        DatosSala(sala_id, "Sala", ())
    with pytest.raises(TypeError):
        DatosSalida("N", sala_id, 1, (2, "N"))
