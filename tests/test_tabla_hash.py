"""C1-6: tabla hash propia (sin dict como índice), con colisiones."""

from src.controller1.lista_doble import Nodo
from src.controller1.tabla_hash import TablaHash


def test_poner_obtener_eliminar():
    t = TablaHash()
    t.poner("a", Nodo("a", 1))
    t.poner("b", Nodo("b", 2))
    assert t.obtener("a").valor == 1
    assert t.obtener("b").valor == 2
    assert t.obtener("zz") is None
    assert "a" in t and "zz" not in t
    assert len(t) == 2
    assert t.eliminar("a") is True
    assert t.eliminar("a") is False
    assert len(t) == 1


def test_actualiza_existente():
    t = TablaHash()
    t.poner("a", Nodo("a", 1))
    t.poner("a", Nodo("a", 99))
    assert t.obtener("a").valor == 99
    assert len(t) == 1


def test_colisiones_con_pocas_cubetas():
    t = TablaHash(cubetas=2)  # fuerza cadenas largas
    for i in range(20):
        t.poner(f"clave-{i}", Nodo(f"clave-{i}", i))
    assert len(t) == 20
    for i in range(20):
        assert t.obtener(f"clave-{i}").valor == i
    t.eliminar("clave-5")
    assert t.obtener("clave-5") is None
    assert len(t) == 19


def test_sin_dict_como_indice():
    dentro_doc = False
    for linea in open("src/controller1/tabla_hash.py"):
        s = linea.strip()
        if s.startswith('"""'):
            dentro_doc = not dentro_doc
            continue
        if dentro_doc or not s or s.startswith("#"):
            continue
        assert "dict" not in s, f"uso prohibido: {s}"


def test_cubetas_invalidas():
    try:
        TablaHash(cubetas=0)
    except ValueError:
        return
    raise AssertionError("debió rechazar 0 cubetas")
