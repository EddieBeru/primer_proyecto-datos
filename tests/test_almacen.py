"""C1: almacén persistente de fichas (§4.3/§4.4 doc oficial).

La LRU en memoria tiene tope; el almacén conserva lo desalojado en disco
(o en memoria si no hay ruta) y sobrevive entre sesiones.
"""

import os

import pytest

from src.controller1.almacen_fichas import MAGIA, AlmacenFichas
from src.models.objects import Potion


def _pocion(pid="p1", cura=5):
    return Potion(id=pid, nombre="Poción", peso=1, valor=1, cura=cura,
                  modificador_velocidad=None, duracion=None)


def test_memoria_roundtrip_sin_ruta():
    al = AlmacenFichas()
    assert not al.contiene("p1") and al.obtener("p1") is None
    al.guardar("p1", _pocion())
    assert al.contiene("p1") and al.obtener("p1").cura == 5
    assert len(al) == 1


def test_disco_roundtrip_reconstruye_indice(tmp_path):
    ruta = str(tmp_path / "almacen.bin")
    al = AlmacenFichas(ruta=ruta, version="v1")
    al.guardar("p1", _pocion("p1", 5))
    al.guardar("p2", _pocion("p2", 9))

    al2 = AlmacenFichas.cargar_disco(ruta)
    assert al2.version == "v1"
    assert al2.contiene("p2") and al2.obtener("p2").cura == 9
    assert al2.obtener("p1").id == "p1"


def test_guardar_reemplaza_por_id(tmp_path):
    ruta = str(tmp_path / "almacen.bin")
    al = AlmacenFichas(ruta=ruta)
    al.guardar("p1", _pocion("p1", 5))
    al.guardar("p1", _pocion("p1", 7))

    al2 = AlmacenFichas.cargar_disco(ruta)
    assert al2.obtener("p1").cura == 7
    assert len(al2) == 1


def test_invalidar_version_vacia_y_trunca(tmp_path):
    ruta = str(tmp_path / "almacen.bin")
    al = AlmacenFichas(ruta=ruta, version="v1")
    al.guardar("p1", _pocion("p1", 5))

    assert al.invalida_si_cambia("v1") is False
    assert al.contiene("p1")

    assert al.invalida_si_cambia("v2") is True
    assert not al.contiene("p1")
    al.guardar("p2", _pocion("p2", 3))

    al2 = AlmacenFichas.cargar_disco(ruta)
    assert al2.version == "v2"
    assert al2.contiene("p2") and not al2.contiene("p1")


def test_archivo_corrupto_error_propio(tmp_path):
    ruta = str(tmp_path / "basura.bin")
    with open(ruta, "wb") as f:
        f.write(b"no soy un almacen")
    with pytest.raises(ValueError):
        AlmacenFichas.cargar_disco(ruta)


def test_cabecera_ok_cola_truncada_se_ignora(tmp_path):
    ruta = str(tmp_path / "almacen.bin")
    al = AlmacenFichas(ruta=ruta, version="v1")
    al.guardar("p1", _pocion("p1", 5))
    al.guardar("p2", _pocion("p2", 9))
    with open(ruta, "rb") as f:
        contenido = f.read()
    with open(ruta, "wb") as f:
        f.write(contenido[:-4])  # corta el último registro a la mitad

    al2 = AlmacenFichas.cargar_disco(ruta)
    assert al2.version == "v1"
    assert al2.obtener("p1").id == "p1"


def test_reabrir_al_cerrar_sin_perder(tmp_path):
    """Cerrar y reabrir el proceso: el índice se rearma desde disco."""
    ruta = str(tmp_path / "almacen.bin")
    al = AlmacenFichas(ruta=ruta, version="v1")
    for i in range(30):
        al.guardar(f"f{i}", _pocion(f"f{i}", i))
    al2 = AlmacenFichas.cargar_disco(ruta)
    assert len(al2) == 30
    assert al2.obtener("f29").cura == 29
    with open(ruta, "rb") as f:
        assert f.read(len(MAGIA)) == MAGIA
    assert os.path.getsize(ruta) > 0
