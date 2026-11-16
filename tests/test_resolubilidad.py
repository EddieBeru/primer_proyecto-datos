"""Escenarios de aceptación del cálculo puro de resolubilidad."""

from types import SimpleNamespace

import pytest

from src.algoritmos.resolubilidad import verificar_resolubilidad
from src.models.resolubilidad import UbicacionesLlaves, UbicacionLlave
from src.orchestrator.reporte_resolubilidad import texto_reporte
from tests.fixtures_resolubilidad import (escenario_resoluble, escenario_ciclo,
    escenario_incompleto, escenario_errante, ubicacion, sala, esqueleto)


def verificar(datos):
    plano, llaves, info = datos
    info = SimpleNamespace(id="caso", version="v1", **info)
    ubic = UbicacionesLlaves("caso", "v1", info.completa if hasattr(info, "completa") else True,
        tuple(UbicacionLlave(x["id"], x["sala"], x["enemigo"]) for x in llaves))
    return verificar_resolubilidad(info, plano, ubic)


def test_escenario1_llave_final_detras_de_su_puerta_no_resoluble():
    r = verificar(escenario_ciclo())
    assert r.estado == "no_resoluble"
    assert r.llaves_no_obtenibles == ("final",)
    assert r.frontera == ((1, "E", 2, "final"),)
    assert r.ciclo == ("final", "final")
    assert "sala 1 / E -> sala 2" in texto_reporte(r)


def test_escenario2_llave_de_errante_en_sala_inicial():
    r = verificar(escenario_errante())
    assert r.estado == "resoluble"
    assert r.orden_llaves[0][1].sala == 1
    assert r.orden_llaves[0][1].enemigo == "enemigo-1"


def test_escenario3_orden_determinista_por_descubrimiento_y_consulta():
    datos = ({1: sala(1, "I", N={"sala": 2}, E={"sala": 3}),
              2: sala(2, "N"), 3: sala(3, "E"), 4: sala(4, "F")},
        (ubicacion("Z", 2), ubicacion("A", 3), ubicacion("fin", 2)),
        {"sala_inicial": 1, "sala_salida": 4, "llave_salida": "fin"})
    a = verificar(datos)
    assert [x[0] for x in a.orden_llaves] == ["Z", "fin", "A"]
    for _ in range(100):
        assert verificar(datos).orden_llaves == a.orden_llaves


def test_escenario5_reutiliza_llave_en_puertas_distintas():
    plano = {1: sala(1, "I", E={"sala": 2, "llave": "paso", "cerrada": True},
                         S={"sala": 3, "llave": "paso", "cerrada": True}),
             2: sala(2, "A"), 3: sala(3, "F", E={"sala": 4, "llave": "fin",
                                                     "cerrada": True}),
             4: sala(4, "Salida")}
    datos = (plano, (ubicacion("paso", 1), ubicacion("fin", 3)),
             {"sala_inicial": 1, "sala_salida": 4, "llave_salida": "fin"})
    assert verificar(datos).estado == "resoluble"


def test_escenario6_usa_salida_y_llave_declaradas_en_info():
    datos = ({100: sala(100, "Inicio", E={"sala": 900, "llave": "x",
                                             "cerrada": True}),
              900: sala(900, "Fin")},
             (ubicacion("x", 100),),
             {"sala_inicial": 100, "sala_salida": 900, "llave_salida": "x"})
    assert verificar(datos).estado == "resoluble"


def test_escenario7_puerta_cerrada_sin_llave_es_error():
    datos = ({1: sala(1, "I", E={"sala": 2, "cerrada": True}), 2: sala(2, "F")},
             (), {"sala_inicial": 1, "sala_salida": 2, "llave_salida": "x"})
    with pytest.raises(ValueError, match="sala 1/E"):
        verificar(datos)


def test_escenario8_llave_requerida_ausente_es_no_obtenible():
    datos = ({1: sala(1, "I", E={"sala": 2, "llave": "x", "cerrada": True}),
              2: sala(2, "F")}, (),
             {"sala_inicial": 1, "sala_salida": 2, "llave_salida": "x"})
    r = verificar(datos)
    assert r.estado == "no_resoluble" and r.llaves_no_obtenibles == ("x",)
    assert r.ubicaciones == ()


def test_escenario8_alternativa_abierta_permite_victoria_sin_llave_opcional():
    datos = ({1: sala(1, "I", N={"sala": 2, "llave": "x", "cerrada": True},
                         E={"sala": 3}),
              2: sala(2, "B"), 3: sala(3, "F", N={"sala": 4, "llave": "final",
                                                     "cerrada": True}),
              4: sala(4, "Salida")}, (ubicacion("final", 3),),
             {"sala_inicial": 1, "sala_salida": 4, "llave_salida": "final"})
    assert verificar(datos).estado == "resoluble"


def test_escenario9_n_antes_de_e_y_llaves_locales_segun_consulta():
    datos = ({1: sala(1, "I", N={"sala": 2}, E={"sala": 3}),
              2: sala(2, "N"), 3: sala(3, "E"), 4: sala(4, "F")},
             (ubicacion("Z", 2), ubicacion("A", 3), ubicacion("local2", 2),
              ubicacion("fin", 2)),
             {"sala_inicial": 1, "sala_salida": 4, "llave_salida": "fin"})
    r = verificar(datos)
    assert [k for k, _ in r.orden_llaves] == ["Z", "local2", "fin", "A"]


def test_consulta_incompleta_no_emite_veredicto():
    r = verificar(escenario_incompleto())
    assert r.estado == "incompleta"


def test_reporte_negativo_sin_ciclo_y_con_categorias_vacias():
    datos = ({1: sala(1, "I"), 99: sala(99, "F")}, (),
             {"sala_inicial": 1, "sala_salida": 99, "llave_salida": "final"})
    reporte = texto_reporte(verificar(datos))
    assert "Frontera bloqueada:\nninguna" in reporte
    assert "Ciclo bloqueante:\nninguno" in reporte
    assert "final: ubicación no declarada" in reporte


def test_escenario13_ciclo_de_alternativas_y_otras_causas():
    plano = {1: sala(1, "I", N={"sala": 2, "llave": "A", "cerrada": True},
                         E={"sala": 3, "llave": "A", "cerrada": True}),
             2: sala(2, "B", N={"sala": 4, "llave": "B", "cerrada": True}),
             3: sala(3, "C", N={"sala": 4, "llave": "C", "cerrada": True}),
             4: sala(4, "A-room", S={"sala": 5, "llave": "fin", "cerrada": True}),
             5: sala(5, "F")}
    datos = (plano, (ubicacion("A", 4), ubicacion("B", 2),
                     ubicacion("C", 3), ubicacion("fin", 5)),
             {"sala_inicial": 1, "sala_salida": 5, "llave_salida": "fin"})
    r = verificar(datos)
    assert r.estado == "no_resoluble"
    assert r.ciclo == ("A", "B", "A")
    assert len(r.alternativas_bloqueadas) >= 2


def test_salidas_automaticas_y_trampas_no_bloquean_y_llave_no_se_consumen():
    plano = {1: sala(1, "I", E={"sala": 2, "llave": "paso", "cerrada": True},
                         S={"sala": 3, "llave": "paso", "cerrada": True}),
             2: sala(2, "Ruta", E={"sala": 4, "llave": "fin", "cerrada": True,
                                      "cierre_automatico": 1}),
             3: sala(3, "Alterna"), 4: sala(4, "Salida")}
    datos = (plano, (ubicacion("paso", 1), ubicacion("fin", 2)),
             {"sala_inicial": 1, "sala_salida": 4, "llave_salida": "fin"})
    r = verificar(datos)
    assert r.estado == "resoluble"
    assert [k for k, _ in r.orden_llaves] == ["paso", "fin"]


def test_ciclos_independientes_solo_reporta_el_primero_segun_consulta():
    plano = {1: sala(1, "I", N={"sala": 2, "llave": "B", "cerrada": True},
                         E={"sala": 3, "llave": "A", "cerrada": True}),
             2: sala(2, "B"), 3: sala(3, "A"), 4: sala(4, "F")}
    datos = (plano, (ubicacion("B", 2), ubicacion("A", 3)),
             {"sala_inicial": 1, "sala_salida": 4, "llave_salida": "fin"})
    r = verificar(datos)
    assert r.ciclo == ("B", "B")
    assert len(r.ciclo) == 2


def test_circuito_abierto_de_salas_aislado_no_es_ciclo_de_llaves():
    plano = {1: sala(1, "I"), 2: sala(2, "A", E={"sala": 3}),
             3: sala(3, "B", O={"sala": 2}), 4: sala(4, "F")}
    datos = (plano, (), {"sala_inicial": 1, "sala_salida": 4,
                         "llave_salida": "fin"})
    r = verificar(datos)
    assert r.estado == "no_resoluble" and r.ciclo == ()
    assert r.frontera == ()


def test_contadores_de_propagacion_quedan_acotados_por_entrada():
    plano = {i: sala(i, str(i), **({"E": {"sala": i + 1}}
                                   if i <= 40 else {})) for i in range(1, 42)}
    datos = (plano, (ubicacion("fin", 40),),
             {"sala_inicial": 1, "sala_salida": 41, "llave_salida": "fin"})
    r = verificar(datos)
    conteos = dict(r.contadores)
    assert conteos["salas"] == len(plano)
    assert conteos["salidas"] == 40
    assert conteos["llaves"] == 1
