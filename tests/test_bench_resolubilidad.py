"""Reproducibilidad y equivalencia de los datos sintéticos del benchmark."""

from src.orchestrator.bench_resolubilidad import (generar_cadena,
    referencia_repetida, correr_bench_resolubilidad, _familia)
from src.algoritmos.resolubilidad import verificar_resolubilidad


def test_generacion_determinista_y_mismo_conjunto_de_entrada():
    a = generar_cadena(12, semilla=300316)
    b = generar_cadena(12, semilla=300316)
    assert a == b
    assert len(a[2].llaves) == 13


def test_referencia_repetida_y_incremental_coinciden_en_cadena_pequena():
    info, plano, ubicaciones = generar_cadena(24, semilla=300316)
    nuevo = verificar_resolubilidad(info, plano, ubicaciones)
    viejo = referencia_repetida(info, plano, ubicaciones)
    assert viejo[0] == nuevo.estado
    assert viejo[1] == tuple(k for k, _ in nuevo.orden_llaves)


def test_bench_reporta_muestras_contadores_y_fases_solicitadas():
    registro = correr_bench_resolubilidad(tamanos=(8,), familias=("cadena",))
    muestra = registro["muestras"][0]
    assert len(muestra["muestras_total_local_ns"]) == 7
    assert muestra["visitas"]
    assert len(muestra["fases_ns"]) == 3
    assert muestra["comparador_repetido"] is not None
    assert muestra["colisiones_ids"] >= 0
    assert muestra["maximo_ids_por_cubeta"] >= 1


def test_bench_incluye_familia_de_puertas_pendientes():
    registro = correr_bench_resolubilidad(tamanos=(8,), familias=("pendientes",))
    muestra = registro["muestras"][0]
    assert muestra["familia"] == "pendientes"
    assert muestra["salidas"] <= 4 * muestra["salas"]


def test_familias_sinteticas_tienen_mismas_entradas_para_ambos_metodos():
    for familia in ("cadena", "ciclo", "pendientes", "alternativas", "desconexion"):
        info, plano, ubicaciones = generar_cadena(10, 300316)
        ubicaciones = _familia(info, plano, ubicaciones, familia, 300316)
        nuevo = verificar_resolubilidad(info, plano, ubicaciones)
        viejo = referencia_repetida(info, plano, ubicaciones)
        assert viejo[0] == nuevo.estado
