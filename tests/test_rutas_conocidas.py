"""Ruta ponderada determinista; sin consultas al grafo vivo ni contenido."""

from src.algoritmos.rutas import siguiente_paso
from src.controller2.conocimiento import MapaConocido
from src.models.conocimiento import DatosSala, DatosSalida


def mapa_de_arcos(arcos):
    mapa = MapaConocido()
    for origen, salidas in arcos:
        datos = tuple(DatosSalida(d, v, c, (origen, d)) for d, v, c in salidas)
        mapa.explorar(DatosSala(origen, str(origen), datos))
        for salida in datos:
            mapa.observar(salida.puerta_id, False)
    return mapa


def test_mas_arcos_menor_costo_y_desempate_descubierto_tarde():
    mapa = mapa_de_arcos([
        (100, [("N", 9, 1), ("S", 2, 3), ("E", 90, 30)]),
        (9, [("E", 90, 9)]), (2, [("E", 7, 1)]),
        (7, [("E", 90, 6)]), (90, []),
    ])
    ruta = siguiente_paso(100, 90, mapa.adyacentes)
    assert (ruta.costo_total, ruta.primer_vecino, ruta.direccion) == (10, 2, "S")


def test_ciclos_costouno_paralelos_y_ids_dispersos():
    mapa = mapa_de_arcos([
        (2, [("E", 10**12, 1), ("N", 10**12, 1)]),
        (10**12, [("S", 2, 1), ("E", 7, 1)]), (7, []),
    ])
    ruta = siguiente_paso(2, 7, mapa.adyacentes)
    assert (ruta.costo_total, ruta.primer_vecino, ruta.direccion) == (2, 10**12, "N")
    assert siguiente_paso(2, 2, mapa.adyacentes).costo_total == 0
    assert not siguiente_paso(7, 2, mapa.adyacentes).alcanzable


def test_avistadas_y_puertas_desconocidas_o_cerradas_no_son_ruta():
    mapa = MapaConocido()
    mapa.explorar(DatosSala(2, "Entrada", (DatosSalida("E", 5, 1, (2, "E")),)))
    assert not siguiente_paso(2, 5, mapa.adyacentes).alcanzable
    mapa.explorar(DatosSala(5, "Vecina", ()))
    assert not siguiente_paso(2, 5, mapa.adyacentes).alcanzable
    mapa.observar((2, "E"), True)
    assert not siguiente_paso(2, 5, mapa.adyacentes).alcanzable
    mapa.observar((2, "E"), False)
    assert siguiente_paso(2, 5, mapa.adyacentes).alcanzable


def test_busqueda_solo_recibe_adyacencia_del_conocimiento(proveedor_niebla):
    mapa = MapaConocido()
    mapa.revelar(2, proveedor_niebla.datos_sala, antorcha=True)
    mapa.observar((2, "E"), False)
    proveedor_niebla.consultas_metadatos.clear()
    with proveedor_niebla.solo_metadatos():
        assert siguiente_paso(2, 5, mapa.adyacentes).alcanzable
    assert proveedor_niebla.consultas_metadatos == []


from fixtures_niebla import proveedor_niebla
