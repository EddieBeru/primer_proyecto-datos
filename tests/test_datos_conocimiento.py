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


def test_datos_salida_comparte_llave_estado_y_costo_default():
    salida = DatosSalida("E", 9, 100, (2, "E"))
    assert salida.llave is None and salida.cerrada_inicial is False
    con_llave = DatosSalida("E", 9, 1, (2, "E"), "llave-A", True)
    assert (con_llave.llave, con_llave.cerrada_inicial, con_llave.costo) == (
        "llave-A", True, 1)


def test_constructor_comun_preserva_orden_fuente_y_puertas_paralelas():
    from src.models.rooms import Exit, Room
    from src.models.conocimiento import preparar_metadatos

    sala = Room(1, "A", {"E": Exit(2), "N": Exit(3), "O": Exit(2)})
    plano = preparar_metadatos((sala, Room(2, "B"), Room(3, "C")))
    assert tuple(x.direccion for x in plano[1].salidas) == ("N", "E", "O")
    assert plano[1].salidas[1].puerta_id != plano[1].salidas[2].puerta_id


def test_constructor_comun_rechaza_reciprocidad_contradictoria():
    from src.models.rooms import Exit, Room
    from src.models.conocimiento import preparar_metadatos

    adelante = Room(1, "A", {"E": Exit(2, llave="llave-a")})
    atras = Room(2, "B", {"O": Exit(1, llave="llave-b")})
    with pytest.raises(ValueError, match="recíprocas"):
        preparar_metadatos((adelante, atras))
