"""Comprobar que los falsos distinguen metadatos y contenido de verdad."""

import pytest

from fixtures_niebla import (
    AISLADA, INICIO, LEJANA, VECINA, crear_jugador_niebla, proveedor_niebla,
)
from src.models.errors import NotFoundError


def test_metadata_no_observa_ni_activa_contenido(proveedor_niebla):
    with proveedor_niebla.solo_metadatos():
        datos = proveedor_niebla.datos_sala(VECINA)
        assert datos.nombre == "Capilla" and len(datos.salidas) == 3
    assert proveedor_niebla.consultas_metadatos == [VECINA]
    assert proveedor_niebla.consultas_contenido == []
    assert proveedor_niebla.consultas_fichas == []
    assert proveedor_niebla.activaciones == []
    sala = proveedor_niebla.sala_lista(VECINA)
    assert not sala.enemigos[0].activa and sala.trampas[0].armada
    assert not sala.visitada


@pytest.mark.parametrize("operacion", ["contenido", "ficha", "activar"])
def test_proteccion_falla_en_acceso_oculto_y_se_restaura(proveedor_niebla, operacion):
    with proveedor_niebla.solo_metadatos():
        with pytest.raises(AssertionError, match="contenido"):
            if operacion == "contenido":
                proveedor_niebla.sala_lista(VECINA)
            elif operacion == "ficha":
                proveedor_niebla.ficha("antorcha")
            else:
                proveedor_niebla.activar(VECINA)
    assert proveedor_niebla.sala_lista(VECINA).id == VECINA


def test_costos_y_puertas_no_funden_arcos_ni_inventan_inversas(proveedor_niebla):
    inicio = proveedor_niebla.datos_sala(INICIO)
    vecina = proveedor_niebla.datos_sala(VECINA)
    assert inicio.salidas[0].puerta_id == vecina.salidas[0].puerta_id
    assert inicio.salidas[0].puerta_id != inicio.salidas[1].puerta_id
    assert all(s.costo > 0 for s in inicio.salidas + vecina.salidas)
    assert proveedor_niebla.datos_sala(AISLADA).salidas == ()
    assert proveedor_niebla.sala_lista(VECINA).salidas["N"].cerrada
    assert proveedor_niebla.sala_lista(LEJANA).salidas["S"].cerrada
    assert not proveedor_niebla.sala_lista(INICIO).salidas["E"].cerrada


def test_enemigos_trampas_consumibles_y_efectos(proveedor_niebla):
    sala = proveedor_niebla.sala_lista(VECINA)
    assert sala.enemigos[0].vivo and not sala.enemigos[0].activa
    assert not sala.enemigos[1].vivo
    assert proveedor_niebla.sala_lista(LEJANA).enemigos[0].activa
    assert proveedor_niebla.ficha("veneno").veneno == 2
    assert proveedor_niebla.ficha("fuego").quemadura == 2
    jugador = crear_jugador_niebla()
    assert "antorcha" in jugador.inventario and jugador.efectos["veneno"] == 400


def test_ids_inexistentes_y_fixtures_independientes(proveedor_niebla):
    from fixtures_niebla import crear_proveedor_niebla

    with pytest.raises(NotFoundError):
        proveedor_niebla.datos_sala(77)
    with pytest.raises(NotFoundError):
        proveedor_niebla.sala_lista(77)
    otro = crear_proveedor_niebla()
    proveedor_niebla.activar(VECINA)
    assert not otro.sala_lista(VECINA).enemigos[0].activa
    assert otro.consultas_metadatos == []
