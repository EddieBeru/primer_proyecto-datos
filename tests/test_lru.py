"""C1-6: LRU (desalojo, tope, recién-usado, versión, disco)."""

import pytest

from src.controller1.lru_cache import CacheLRU


def test_desalojo_menos_usado():
    c = CacheLRU(capacidad=2)
    c.guardar("a", "fa")
    c.guardar("b", "fb")
    assert c.obtener("a") == "fa"  # a al frente, b queda cola
    c.guardar("c", "fc")           # llena: sale b, no a
    assert c.obtener("a") == "fa"
    assert c.obtener("b") is None
    assert c.obtener("c") == "fc"


def test_tope_nunca_excede():
    c = CacheLRU(capacidad=3)
    for i in range(10):
        c.guardar(f"k{i}", i)
    assert len(c) == 3
    assert set(n.clave for n in c._orden) == {"k9", "k8", "k7"}


def test_actualizar_promueve():
    c = CacheLRU(capacidad=2)
    c.guardar("a", 1)
    c.guardar("b", 2)
    c.guardar("a", 99)  # actualiza y promueve
    c.guardar("c", 3)   # sale b
    assert c.obtener("a") == 99
    assert c.obtener("b") is None


def test_miss_retorna_none():
    assert CacheLRU(capacidad=2).obtener("x") is None


def test_capacidad_invalida():
    with pytest.raises(ValueError):
        CacheLRU(capacidad=0)


def test_version_igual_reutiliza_distinta_invalida():
    c = CacheLRU(capacidad=2, version="v1")
    c.guardar("a", 1)
    assert c.invalida_si_cambia("v1") is False
    assert c.obtener("a") == 1
    assert c.invalida_si_cambia("v2") is True
    assert len(c) == 0 and c.version == "v2"


def test_disco_ida_y_vuelta(tmp_path):
    ruta = str(tmp_path / "cache.pkl")
    c = CacheLRU(capacidad=3, version="v7")
    c.guardar("a", 1)
    c.guardar("b", 2)
    c.obtener("a")  # orden: a, b
    c.guardar_disco(ruta)
    d = CacheLRU.cargar_disco(ruta, capacidad=3)
    assert d.version == "v7"
    assert [n.clave for n in d._orden] == ["a", "b"]
    assert d.obtener("b") == 2


def test_disco_respeta_nueva_capacidad(tmp_path):
    ruta = str(tmp_path / "cache.pkl")
    c = CacheLRU(capacidad=5, version="v1")
    for k in ["a", "b", "c", "d"]:
        c.guardar(k, k)
    c.guardar_disco(ruta)
    d = CacheLRU.cargar_disco(ruta, capacidad=2)
    assert [n.clave for n in d._orden] == ["d", "c"]  # las 2 más recientes


def test_disco_danado_lanza_error(tmp_path):
    ruta = str(tmp_path / "cache.pkl")
    with open(ruta, "wb") as f:
        f.write(b"basura-no-pickle")
    with pytest.raises(Exception):
        CacheLRU.cargar_disco(ruta, capacidad=2)
