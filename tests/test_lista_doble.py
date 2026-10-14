"""C1-6: lista doble (orden ambos sentidos, mover al frente, sacar cola)."""

from src.adapters.lista_doble import ListaDoble, Nodo


def test_agregar_y_recorrer():
    l = ListaDoble()
    a, b, c = Nodo("a", 1), Nodo("b", 2), Nodo("c", 3)
    l.agregar_frente(a)
    l.agregar_frente(b)
    l.agregar_frente(c)
    assert [n.clave for n in l] == ["c", "b", "a"]
    assert [n.clave for n in l.hacia_atras()] == ["a", "b", "c"]
    assert len(l) == 3


def test_mover_frente():
    l = ListaDoble()
    a, b, c = Nodo("a", 1), Nodo("b", 2), Nodo("c", 3)
    for n in (a, b, c):
        l.agregar_frente(n)
    l.mover_frente(a)  # cola al frente
    assert [n.clave for n in l] == ["a", "c", "b"]
    l.mover_frente(a)  # ya al frente, sin cambio
    assert [n.clave for n in l] == ["a", "c", "b"]
    assert len(l) == 3


def test_sacar_cola():
    l = ListaDoble()
    assert l.sacar_cola() is None
    a, b = Nodo("a", 1), Nodo("b", 2)
    l.agregar_frente(a)
    l.agregar_frente(b)
    assert l.sacar_cola().clave == "a"
    assert [n.clave for n in l] == ["b"]
    assert len(l) == 1


def test_quitar_medio():
    l = ListaDoble()
    a, b, c = Nodo("a", 1), Nodo("b", 2), Nodo("c", 3)
    for n in (a, b, c):
        l.agregar_frente(n)
    l.quitar(c)  # cabeza
    l.quitar(a)  # cola
    assert [n.clave for n in l] == ["b"]
    assert [n.clave for n in l.hacia_atras()] == ["b"]
