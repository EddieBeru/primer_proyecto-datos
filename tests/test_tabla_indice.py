"""Comportamiento del índice propio usado por conocimiento y rutas."""

import pytest

from src.estructuras.tabla_indice import TablaIndice


def test_consulta_reemplazo_y_ausencia():
    tabla = TablaIndice()
    assert len(tabla) == 0
    assert tabla.obtener(9) is None
    with pytest.raises(KeyError):
        _ = tabla[9]
    tabla[9] = "sala"
    tabla[9] = "observada"
    assert tabla[9] == "observada"
    assert len(tabla) == 1 and 9 in tabla
    assert tabla.obtener(10, "ausente") == "ausente"


def test_colisiones_borrado_y_reinsercion():
    # Buscar claves que colisionan con la capacidad inicial, sin suponer hash nativo.
    tabla = TablaIndice(capacidad=8)
    claves = []
    for clave in range(1000):
        if tabla._indice(clave) == tabla._indice(0):
            claves.append(clave)
        if len(claves) == 4:
            break
    assert len(claves) == 4
    for clave in claves:
        tabla[clave] = f"sala {clave}"
    # Eliminar primero un nodo intermedio y luego el resto de la cadena.
    assert tabla.borrar(claves[1])
    assert not tabla.borrar(claves[1])
    for clave in (claves[0], claves[2], claves[3]):
        assert tabla[clave] == f"sala {clave}"
    tabla[claves[1]] = "restaurada"
    assert tabla[claves[1]] == "restaurada"
    for clave in claves:
        del tabla[clave]
    assert len(tabla) == 0 and list(tabla.items()) == []
    with pytest.raises(KeyError):
        del tabla[claves[0]]


def test_expansion_al_superar_tres_cuartos_y_reemplazo_no_expande():
    tabla = TablaIndice(capacidad=4)
    for clave in (1, 2, 3):
        tabla[clave] = clave * 10
    assert tabla.capacidad == 4
    tabla[3] = 99
    assert tabla.capacidad == 4
    tabla[4] = 40
    assert tabla.capacidad == 8
    assert [tabla[n] for n in (1, 2, 3, 4)] == [10, 20, 99, 40]


def test_ids_dispersos_extremos_y_expansiones_sucesivas():
    tabla = TablaIndice(capacidad=4)
    claves = [-(10**12), 0, 10**12, (10**12, "N"), (10**12, "S")]
    claves.extend(10**20 + i * 1000003 for i in range(150))
    for i, clave in enumerate(claves):
        tabla[clave] = i
    assert len(tabla) == len(claves)
    assert tabla.capacidad < 1024  # Nunca reservar hasta el ID máximo.
    assert [tabla[clave] for clave in claves] == list(range(len(claves)))
    assert len(list(tabla.items())) == len(claves)
    for clave in claves[::2]:
        assert tabla.borrar(clave)
    for clave in claves[1::2]:
        assert clave in tabla


@pytest.mark.parametrize("clave", [True, "1", 1.0, (1, "X"), (True, "N"), (1, 2), (1,)])
def test_rechaza_claves_invalidas_sin_normalizarlas(clave):
    tabla = TablaIndice()
    with pytest.raises((TypeError, ValueError)):
        tabla[clave] = 1
    assert len(tabla) == 0


def test_hash_determinista_en_instancias_independientes():
    a, b = TablaIndice(), TablaIndice()
    for clave in (0, -1, 10**30, (7, "O")):
        assert a._indice(clave) == b._indice(clave)
