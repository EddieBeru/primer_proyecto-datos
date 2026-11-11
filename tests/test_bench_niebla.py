"""La alternativa medida conserva la decisión y las cuentas incluyen rehash."""
import pytest
from src.algoritmos.rutas import siguiente_paso
from src.orchestrator.bench_niebla import crear_mapa, ruta_lineal, IndiceContado


@pytest.mark.parametrize('forma', ['cadena', 'malla', 'empates'])
@pytest.mark.parametrize('parcial', [False, True])
@pytest.mark.parametrize('cierres', [False, True])
def test_alternativas_equivalentes(forma, parcial, cierres):
    mapa = crear_mapa(100, forma, parcial, cierres)
    for destino in (0, 3, 49, 99):
        assert siguiente_paso(0, destino, mapa.adyacentes) == ruta_lineal(0, destino, mapa.adyacentes)


def test_contador_incluye_expansiones():
    indice = IndiceContado()
    for i in range(100):
        indice[i] = i
    assert indice.expansiones == 5
    assert indice.rehash_registros == 6+12+24+48+96
    assert indice.escrituras == 100
    assert all(indice[i] == i for i in range(100))


def test_carga_desactualizada_separa_estado_fisico_y_memoria():
    mapa = crear_mapa(100, 'malla', desactualizada=True)
    assert all(cerrada is False for _, cerrada in mapa.puertas_vivas_bench)
    assert any(mapa.puerta(clave) == 'cerrada' for clave, _ in mapa.puertas_vivas_bench)


@pytest.mark.parametrize('forma', ['cadena','malla','empates'])
def test_sinteticos_respetan_costos_reciprocos_y_grado(forma):
    mapa = crear_mapa(100, forma)
    for sala in mapa.salas():
        assert len(sala.salidas) <= 4
        for salida in sala.salidas:
            inversa = next(s for s in mapa.sala(salida.destino).salidas if s.destino == sala.id)
            assert (inversa.costo, inversa.puerta_id) == (salida.costo, salida.puerta_id)
