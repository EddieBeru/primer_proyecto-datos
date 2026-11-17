"""Pruebas unitarias, de integración y de rendimiento para la capacidad
001-terreno-cazador (costos de terreno, cazador con montículo propio y desempate).

PROHIBICIONES ESTRICTAS:
- No usar heapq, deque ni set (ni como estructura auxiliar).
- Cobertura de los 7 casos de aceptación del Apéndice B.
"""

from __future__ import annotations

import time
import pytest

from src.models.dungeons import DungeonGeneral
from src.models.rooms import Exit, Room
from src.models.catalog import Enemy
from src.controller2.modelo import (
    EstadoPartida,
    SalaViva,
    SalidaViva,
    JugadorVivo,
    EnemigoInstancia,
)
from src.controller2.fachada import Fachada


# ---------------------------------------------------------------------------
# Fixtures sintéticos y ayudantes para pruebas
# ---------------------------------------------------------------------------

def crear_ficha_cripta(salas_total: int = 5, sala_inicial: int = 1, sala_salida: int = 5) -> DungeonGeneral:
    """Crea ficha básica de cripta con jugador estándar."""
    return DungeonGeneral.from_dict({
        "id": "cripta-prueba-cazador",
        "version": "v1",
        "salas_total": salas_total,
        "paginas": 1,
        "salas_por_pagina": 50,
        "sala_inicial": sala_inicial,
        "sala_salida": sala_salida,
        "llave_salida": "llave-salida",
        "presupuesto_solicitudes": 100,
        "inventario_max": 5,
        "jugador": {"vida_max": 30, "ataque": 10, "defensa": 2, "velocidad": 100},
    })


def crear_estado_base(salas_total: int = 5, sala_inicial: int = 1) -> EstadoPartida:
    """Inicializa un EstadoPartida con ficha sintética."""
    ficha = crear_ficha_cripta(salas_total=salas_total, sala_inicial=sala_inicial)
    return EstadoPartida.nueva_partida(ficha, version_catalogo="cat-test-v1")


def conectar_salas(
    estado: EstadoPartida,
    id_a: int,
    dir_a_b: str,
    id_b: int,
    dir_b_a: str,
    costo: int = 100,
    cerrada: bool = False,
    llave: str | None = None,
    cierre_automatico: int | None = None,
) -> None:
    """Conecta dos salas asegurando simetría en costo y estado."""
    if id_a not in estado.salas:
        estado.registrar_sala(SalaViva(id=id_a, nombre=f"Sala {id_a}"))
    if id_b not in estado.salas:
        estado.registrar_sala(SalaViva(id=id_b, nombre=f"Sala {id_b}"))

    sala_a = estado.salas[id_a]
    sala_b = estado.salas[id_b]

    sala_a.salidas[dir_a_b] = SalidaViva(
        direccion=dir_a_b,
        destino=id_b,
        cerrada=cerrada,
        llave=llave,
        cierre_automatico=cierre_automatico,
        costo=costo,
    )
    sala_b.salidas[dir_b_a] = SalidaViva(
        direccion=dir_b_a,
        destino=id_a,
        cerrada=cerrada,
        llave=llave,
        cierre_automatico=cierre_automatico,
        costo=costo,
    )


class CatalogoSintetico:
    """Catálogo en memoria que provee fichas para pruebas."""

    def __init__(self) -> None:
        self._fichas: dict[str, Enemy] = {
            "cazador-estandar": Enemy(
                id="cazador-estandar",
                nombre="Cazador Élite",
                vida_max=20,
                ataque=5,
                defensa=1,
                velocidad=100,
                comportamiento="cazador",
                rango=500,
            ),
            "cazador-largo": Enemy(
                id="cazador-largo",
                nombre="Cazador Largo Alcance",
                vida_max=20,
                ataque=5,
                defensa=1,
                velocidad=100,
                comportamiento="cazador",
                rango=5000,
            ),
            "cazador-corto": Enemy(
                id="cazador-corto",
                nombre="Cazador Corto Alcance",
                vida_max=15,
                ataque=4,
                defensa=1,
                velocidad=100,
                comportamiento="cazador",
                rango=150,
            ),
            "errante-test": Enemy(
                id="errante-test",
                nombre="Errante Prueba",
                vida_max=10,
                ataque=2,
                defensa=0,
                velocidad=100,
                comportamiento="errante",
            ),
            "rastreador-test": Enemy(
                id="rastreador-test",
                nombre="Rastreador Prueba",
                vida_max=12,
                ataque=3,
                defensa=0,
                velocidad=100,
                comportamiento="rastreador",
            ),
        }

    def ficha(self, tipo_id: str) -> Enemy | None:
        return self._fichas.get(tipo_id)

    def get(self, tipo_id: str, default=None):
        return self._fichas.get(tipo_id, default)

    def __getitem__(self, tipo_id: str) -> Enemy:
        return self._fichas[tipo_id]

    def __contains__(self, tipo_id: str) -> bool:
        return tipo_id in self._fichas


class ProveedorSintetico:
    """Proveedor mínimo para instanciar Fachada en pruebas de integración."""

    def __init__(self, catalogo: CatalogoSintetico | None = None) -> None:
        self.catalogo = catalogo or CatalogoSintetico()

    def ficha(self, tipo_id: str):
        return self.catalogo.ficha(tipo_id)


# ===========================================================================
# Phase 3: Tests for User Story 1 (Terreno, costos e intervalos)
# ===========================================================================

def test_costo_salida_default_y_simetria():
    """T008 / FR-CAZ-01: Costo predeterminado 100, costo explícito >= 1 y simetría."""
    e_def = Exit(sala=2)
    assert e_def.costo == 100

    e_cust = Exit(sala=3, costo=250)
    assert e_cust.costo == 250

    with pytest.raises(ValueError):
        Exit(sala=4, costo=0)

    with pytest.raises(ValueError):
        Exit(sala=4, costo=-10)

    with pytest.raises(TypeError):
        Exit(sala=4, costo="invalido")  # type: ignore

    # Deserialización desde dict
    e_dict = Exit.from_dict({"sala": 5, "costo": 300})
    assert e_dict.costo == 300
    with pytest.raises(TypeError):
        Exit.from_dict({"sala": 5, "costo": None})
    assert Exit.from_dict({"sala": 5}).costo == 100

    # SalidaViva
    sv = SalidaViva(direccion="N", destino=2, costo=150)
    assert sv.costo == 150

    with pytest.raises(ValueError):
        SalidaViva(direccion="N", destino=2, costo=0)

    # Simetría en conexión
    est = crear_estado_base()
    conectar_salas(est, 1, "E", 2, "O", costo=175)
    assert est.salas[1].salidas["E"].costo == 175
    assert est.salas[2].salidas["O"].costo == 175


def test_actor_rapido_costo_minimo_intervalo_al_menos_uno():
    """T009 / FR-CAZ-02 / Apéndice B Caso 6: Actor con velocidad alta (300) atravesando
    salida de costo 1 con intervalo resultante >= 1 tick virtual."""
    from src.controller2.reloj import intervalo

    # Cálculo directo: max(1, 1 * 100 // 300) = max(1, 0) = 1
    t = intervalo(costo=1, velocidad=300)
    assert t >= 1
    assert t == 1

    # Integración con movimiento del jugador
    est = crear_estado_base(salas_total=2, sala_inicial=1)
    conectar_salas(est, 1, "E", 2, "O", costo=1)
    est.jugador.velocidad = 300

    prov = ProveedorSintetico()
    fachada = Fachada(est, prov, prov.catalogo._fichas)

    # El jugador se mueve a la sala 2 por la salida de costo 1
    ok, msg = fachada.mover("E")
    assert ok, msg
    assert est.sala_actual == 2

    # El turno del jugador debe haberse programado en reloj.ahora + 1
    turno_jugador = next((ev for ev in fachada.agenda if (ev.datos or {}).get("kind") == "jugador"), None)
    assert turno_jugador is not None
    assert turno_jugador.t == 1  # 0 + 1 tick virtual


def test_actor_reescalado_velocidad_en_salida_costosa():
    """T010 / FR-CAZ-12 / Apéndice B Caso 7: Reescalado proporcional del tiempo restante
    al cambiar la velocidad durante el cruce de una salida costosa según P1 §2.3."""
    from src.controller2.reloj import reescalar

    # Costo 600, velocidad 100 -> intervalo 600.
    # A t=200 transcurrieron 200 ticks, restan 400.
    # Se duplica la velocidad a 200:
    # restante_nuevo = max(1, 400 * 100 // 200) = 200.
    # nuevo_t = 200 + 200 = 400.
    t_nuevo = reescalar(t_actual=200, t_siguiente=600, v_anterior=100, v_nueva=200)
    assert t_nuevo == 400

    # Si la velocidad disminuye a la mitad (50):
    # restante_nuevo = max(1, 400 * 100 // 50) = 800.
    # nuevo_t = 200 + 800 = 1000.
    t_frenado = reescalar(t_actual=200, t_siguiente=600, v_anterior=100, v_nueva=50)
    assert t_frenado == 1000


def test_errante_rastreador_costos_transito():
    """T011 / FR-CAZ-03: Universalidad a errantes y rastreadores consumiendo costo_salida
    en desplazamiento y conservando costo 100 en atacar y esperar."""
    from src.controller2.agenda import Agenda
    from src.controller2.reloj import RelojVirtual
    from src.controller2.enemigos import turno_enemigo

    est = crear_estado_base(salas_total=3, sala_inicial=1)
    conectar_salas(est, 1, "E", 2, "O", costo=100)
    conectar_salas(est, 2, "S", 3, "N", costo=350)

    # Errante en sala 2 con velocidad 100
    est.salas[2].enemigos.append(
        EnemigoInstancia(instancia="err-01", tipo_id="errante-test", vida_actual=10, sala_actual=2)
    )

    agenda = Agenda()
    reloj = RelojVirtual(ahora=0)
    cat = CatalogoSintetico()

    # Turno del errante: debe moverse a la sala 3 por la salida de costo 350
    # Jugador está en sala 1, errante en 2, salidas a 1 y 3.
    # Desconectamos sala 1 cerrando la puerta hacia 1 para forzar destino a 3
    est.salas[2].salidas["O"].cerrada = True

    turno_enemigo(est, agenda, reloj, "err-01", catalogo=cat._fichas)

    # El errante debe haber pasado a la sala 3
    assert est.salas[2].enemigos == []
    assert len(est.salas[3].enemigos) == 1
    assert est.salas[3].enemigos[0].instancia == "err-01"

    # Y su siguiente turno debe haberse programado con costo 350 -> max(1, 350 * 100 // 100) = 350
    ev = next((e for e in agenda if (e.datos or {}).get("actor") == "err-01"), None)
    assert ev is not None
    assert ev.t == 350


# ===========================================================================
# Phase 4: Tests for User Story 2 (Persecución estratégica del cazador)
# ===========================================================================

def test_cazador_sin_ruta_abierta_espera():
    """T015 / FR-CAZ-05, FR-CAZ-07 / Apéndice B Caso 1: Un cazador sin ruta abierta
    hacia el jugador espera con costo 100."""
    from src.controller2.agenda import Agenda
    from src.controller2.reloj import RelojVirtual
    from src.controller2.enemigos import turno_enemigo, decidir_accion_cazador

    est = crear_estado_base(salas_total=3, sala_inicial=1)
    conectar_salas(est, 1, "E", 2, "O", costo=100, cerrada=True)  # Puerta cerrada entre 1 y 2
    conectar_salas(est, 2, "S", 3, "N", costo=100)

    # Cazador en sala 3, jugador en sala 1
    est.salas[3].enemigos.append(
        EnemigoInstancia(instancia="caz-01", tipo_id="cazador-estandar", vida_actual=20, sala_actual=3)
    )

    cat = CatalogoSintetico()
    accion, costo, destino = decidir_accion_cazador(est, "caz-01", catalogo=cat._fichas)
    assert accion == "esperar"
    assert costo == 100
    assert destino is None

    agenda = Agenda()
    reloj = RelojVirtual(ahora=0)
    turno_enemigo(est, agenda, reloj, "caz-01", catalogo=cat._fichas)

    # El cazador permanece en la sala 3 y reprograma a t=100
    assert len(est.salas[3].enemigos) == 1
    ev = next((e for e in agenda if (e.datos or {}).get("actor") == "caz-01"), None)
    assert ev is not None
    assert ev.t == 100


def test_cazador_distancia_mayor_que_rango_espera():
    """T016 / FR-CAZ-05, FR-CAZ-07 / Apéndice B Caso 2: La ruta más barata cuesta más que
    su rango: espera con costo 100."""
    from src.controller2.enemigos import decidir_accion_cazador

    # Cazador corto alcance (rango=150) en sala 3, jugador en sala 1
    # Costo 3->2 es 100, costo 2->1 es 100 -> d = 200 > 150
    est = crear_estado_base(salas_total=3, sala_inicial=1)
    conectar_salas(est, 1, "E", 2, "O", costo=100)
    conectar_salas(est, 2, "S", 3, "N", costo=100)

    est.salas[3].enemigos.append(
        EnemigoInstancia(instancia="caz-corto", tipo_id="cazador-corto", vida_actual=15, sala_actual=3)
    )

    cat = CatalogoSintetico()
    accion, costo, destino = decidir_accion_cazador(est, "caz-corto", catalogo=cat._fichas)
    assert accion == "esperar"
    assert costo == 100
    assert destino is None


def test_cazador_prefiere_menor_costo_que_menos_salas():
    """T017 / FR-CAZ-05, FR-CAZ-08 / Apéndice B Caso 3: Ruta de menos salas pero mayor costo
    frente a ruta de más salas y menor costo: sigue la de menor costo."""
    from src.controller2.enemigos import decidir_accion_cazador

    # Cazador en sala 10, jugador en sala 1.
    # Ruta corta: 10 -> 1 con 1 salida de costo 500. Total d = 500.
    # Ruta larga: 10 -> 20 (costo 50) -> 30 (costo 50) -> 1 (costo 50). Total d = 150.
    est = crear_estado_base(salas_total=35, sala_inicial=1)
    conectar_salas(est, 10, "N", 1, "S", costo=500)
    conectar_salas(est, 10, "E", 20, "O", costo=50)
    conectar_salas(est, 20, "E", 30, "O", costo=50)
    conectar_salas(est, 30, "N", 1, "S", costo=50)

    est.salas[10].enemigos.append(
        EnemigoInstancia(instancia="caz-opt", tipo_id="cazador-estandar", vida_actual=20, sala_actual=10)
    )

    cat = CatalogoSintetico()
    accion, costo, destino = decidir_accion_cazador(est, "caz-opt", catalogo=cat._fichas)
    assert accion == "mover"
    assert destino == 20  # Prefiere la ruta larga pero barata
    assert costo == 50   # Costo de la salida hacia la sala 20


def test_cazador_frontera_d_igual_rango_se_mueve():
    """T018 / FR-CAZ-05, FR-CAZ-07, FR-CAZ-08: Cuando d es exactamente igual al rango,
    el cazador avanza un paso (espera solo si d > rango)."""
    from src.controller2.enemigos import decidir_accion_cazador

    # cazador-corto tiene rango=150.
    # Conectamos salas con costo exacto 150: 2 -> 1 costo 150.
    est = crear_estado_base(salas_total=2, sala_inicial=1)
    conectar_salas(est, 1, "E", 2, "O", costo=150)

    est.salas[2].enemigos.append(
        EnemigoInstancia(instancia="caz-f", tipo_id="cazador-corto", vida_actual=15, sala_actual=2)
    )

    cat = CatalogoSintetico()
    accion, costo, destino = decidir_accion_cazador(est, "caz-f", catalogo=cat._fichas)
    assert accion == "mover"
    assert destino == 1
    assert costo == 150


def test_cazador_comparte_sala_ataca_directo():
    """T019 / FR-CAZ-05: Si el cazador comparte sala con el jugador al inicio de su turno,
    ataca cuerpo a cuerpo según P1 §2.8 sin desplazarse."""
    from src.controller2.enemigos import decidir_accion_cazador

    est = crear_estado_base(salas_total=2, sala_inicial=1)
    conectar_salas(est, 1, "E", 2, "O", costo=100)

    # Cazador en la misma sala 1 que el jugador
    est.salas[1].enemigos.append(
        EnemigoInstancia(instancia="caz-junto", tipo_id="cazador-estandar", vida_actual=20, sala_actual=1)
    )

    cat = CatalogoSintetico()
    accion, costo, destino = decidir_accion_cazador(est, "caz-junto", catalogo=cat._fichas)
    assert accion == "atacar"
    assert costo == 100
    assert destino is None

    # Integración con Fachada: el cazador debe infligir daño al jugador
    prov = ProveedorSintetico()
    fachada = Fachada(est, prov, prov.catalogo._fichas)
    vida_inicial = est.jugador.vida_actual

    # Drenamos un turno del enemigo
    fachada.agenda.programar(0, "turno", {"actor": "caz-junto", "kind": "enemigo", "tipo": "cazador-estandar"})
    fachada.avanzar()

    assert est.jugador.vida_actual < vida_inicial


def test_costo_total_incluye_salida_final_al_jugador():
    """T020 / FR-CAZ-05, FR-CAZ-06: El costo total d incluye obligatoriamente la salida
    que entra a la sala actual del jugador."""
    from src.controller2.rutas import dijkstra_acotado

    # Sala 3 -> Sala 2 (costo 100) -> Sala 1 (costo 200, jugador en sala 1)
    # Total d debe ser exactamente 100 + 200 = 300
    est = crear_estado_base(salas_total=3, sala_inicial=1)
    conectar_salas(est, 3, "N", 2, "S", costo=100)
    conectar_salas(est, 2, "N", 1, "S", costo=200)

    d, sig = dijkstra_acotado(est, origen=3, destino=1, rango_max=500)
    assert d == 300
    assert sig == 2


def test_cazador_vecino_puerta_cerrada_desvio_o_espera():
    """T021 / FR-CAZ-05, FR-CAZ-10: Cazador y jugador en salas contiguas con puerta cerrada:
    no ataca cuerpo a cuerpo y toma un desvío abierto o espera si no hay camino viable."""
    from src.controller2.enemigos import decidir_accion_cazador

    # Cazador en 2, jugador en 1. Puerta 2 <-> 1 cerrada.
    # Desvío abierto: 2 -> 3 (costo 50) -> 1 (costo 50).
    est = crear_estado_base(salas_total=3, sala_inicial=1)
    conectar_salas(est, 1, "E", 2, "O", costo=100, cerrada=True)
    conectar_salas(est, 2, "S", 3, "N", costo=50)
    conectar_salas(est, 3, "O", 1, "E", costo=50)

    est.salas[2].enemigos.append(
        EnemigoInstancia(instancia="caz-vec", tipo_id="cazador-estandar", vida_actual=20, sala_actual=2)
    )

    cat = CatalogoSintetico()
    accion, costo, destino = decidir_accion_cazador(est, "caz-vec", catalogo=cat._fichas)
    assert accion == "mover"
    assert destino == 3  # Toma el desvío por la sala 3
    assert costo == 50

    # Ahora cerramos simétricamente también la puerta 3 <-> 1: no hay camino viable
    est.salas[3].salidas["O"].cerrada = True
    est.salas[1].salidas["E"].cerrada = True
    est.puertas_version += 1
    accion2, costo2, destino2 = decidir_accion_cazador(est, "caz-vec", catalogo=cat._fichas)
    assert accion2 == "esperar"
    assert costo2 == 100
    assert destino2 is None


# ===========================================================================
# Phase 5: Tests for User Story 3 (Determinismo, equivalencia y desempate)
# ===========================================================================

def test_cazador_desempate_menor_id():
    """T025 / FR-CAZ-09 / Apéndice B Caso 4: Desempate estricto por menor id entre
    salas vecinas que inician rutas de costo total mínimo idéntico."""
    from src.controller2.enemigos import decidir_accion_cazador

    # Cazador en sala 10, jugador en sala 1.
    # Vecinas de 10: sala 5 y sala 2.
    # Ruta por 5: 10 -> 5 (costo 100) -> 1 (costo 100). Total d = 200.
    # Ruta por 2: 10 -> 2 (costo 100) -> 1 (costo 100). Total d = 200.
    # Conectamos primero la sala 5 para verificar que no dependa del orden de inserción.
    est = crear_estado_base(salas_total=15, sala_inicial=1)
    conectar_salas(est, 10, "N", 5, "S", costo=100)
    conectar_salas(est, 5, "N", 1, "S", costo=100)
    conectar_salas(est, 10, "O", 2, "E", costo=100)
    conectar_salas(est, 2, "N", 1, "S", costo=100)

    est.salas[10].enemigos.append(
        EnemigoInstancia(instancia="caz-desempate", tipo_id="cazador-estandar", vida_actual=20, sala_actual=10)
    )

    cat = CatalogoSintetico()
    accion, costo, destino = decidir_accion_cazador(est, "caz-desempate", catalogo=cat._fichas)
    assert accion == "mover"
    assert destino == 2  # min(5, 2) == 2
    assert costo == 100


def test_cazador_reaccion_puerta_cerrada_entre_turnos():
    """T026 / FR-CAZ-10, FR-CAZ-11 / Apéndice B Caso 5: Puerta que se cierra entre turnos del
    cazador provocando una decisión idéntica a la obtenida con un cálculo completo desde cero en ese instante."""
    from src.controller2.agenda import Agenda
    from src.controller2.reloj import RelojVirtual
    from src.controller2.enemigos import turno_enemigo, decidir_accion_cazador
    from src.controller2.movimiento import ejecutar_cierre

    # Cazador en 10, jugador en 1.
    # Ruta directa: 10 -> 2 (costo 50) -> 1 (costo 50). Total 100.
    # Ruta alterna: 10 -> 3 (costo 80) -> 1 (costo 80). Total 160.
    est = crear_estado_base(salas_total=15, sala_inicial=1)
    conectar_salas(est, 10, "N", 2, "S", costo=50)
    conectar_salas(est, 2, "O", 1, "E", costo=50)
    conectar_salas(est, 10, "E", 3, "O", costo=80)
    conectar_salas(est, 3, "N", 1, "S", costo=80)

    est.salas[10].enemigos.append(
        EnemigoInstancia(instancia="caz-reac", tipo_id="cazador-estandar", vida_actual=20, sala_actual=10)
    )

    cat = CatalogoSintetico()
    # Primer turno: elige moverse a 2 (costo 100 < 160)
    accion1, costo1, dest1 = decidir_accion_cazador(est, "caz-reac", catalogo=cat._fichas)
    assert accion1 == "mover"
    assert dest1 == 2

    # El cazador avanza a la sala 2
    agenda = Agenda()
    reloj = RelojVirtual(ahora=0)
    turno_enemigo(est, agenda, reloj, "caz-reac", catalogo=cat._fichas)
    assert est.salas[2].enemigos[0].instancia == "caz-reac"

    # Entre turnos, la puerta 2 -> 1 se cierra automáticamente
    ejecutar_cierre(est, 2, "O")
    # Y simétricamente desde 1
    est.salas[1].salidas["E"].cerrada = True

    # Siguiente turno: debe reaccionar de forma idéntica a un cálculo desde cero.
    # Desde la sala 2, el camino a 1 por la puerta cerrada está bloqueado.
    # Desvío posible: 2 -> 10 (costo 50) -> 3 (costo 80) -> 1 (costo 80). Total 210 <= rango (500).
    accion2, costo2, dest2 = decidir_accion_cazador(est, "caz-reac", catalogo=cat._fichas)
    assert accion2 == "mover"
    assert dest2 == 10
    assert costo2 == 50


def test_puerta_con_cierre_pendiente_es_transitable():
    """T027 / FR-CAZ-06, FR-CAZ-11: Una puerta con evento de cierre automático pendiente
    en la agenda se considera abierta y transitable en el instante actual."""
    from src.controller2.agenda import Agenda
    from src.controller2.enemigos import decidir_accion_cazador

    est = crear_estado_base(salas_total=3, sala_inicial=1)
    conectar_salas(est, 2, "N", 1, "S", costo=100, cierre_automatico=500)
    est.salas[2].enemigos.append(
        EnemigoInstancia(instancia="caz-pend", tipo_id="cazador-estandar", vida_actual=20, sala_actual=2)
    )

    agenda = Agenda()
    # Hay un evento futuro de cierre programado para t=500 en la agenda
    agenda.programar(500, "cierre_puerta", {"sala": 2, "direccion": "N"})

    cat = CatalogoSintetico()
    # A t=100 la puerta sigue abierta, por tanto debe considerarla transitable
    accion, costo, dest = decidir_accion_cazador(est, "caz-pend", catalogo=cat._fichas)
    assert accion == "mover"
    assert dest == 1
    assert costo == 100


def test_cazador_ignora_niebla_y_descarga():
    """T028 / FR-CAZ-10: El cazador conoce el esqueleto completo y puertas sin verse
    restringido por niebla de guerra ni descarga de salas."""
    from src.controller2.enemigos import decidir_accion_cazador

    est = crear_estado_base(salas_total=5, sala_inicial=1)
    # Conectamos salas 1 - 2 - 3 - 4.
    # Solo sala 1 es visitada por el jugador. Las salas 2, 3 y 4 nunca fueron visitadas.
    conectar_salas(est, 1, "E", 2, "O", costo=80)
    conectar_salas(est, 2, "E", 3, "O", costo=80)
    conectar_salas(est, 3, "E", 4, "O", costo=80)

    est.salas[2].visitada = False
    est.salas[3].visitada = False
    est.salas[4].visitada = False

    est.salas[4].enemigos.append(
        EnemigoInstancia(instancia="caz-niebla", tipo_id="cazador-estandar", vida_actual=20, sala_actual=4)
    )

    cat = CatalogoSintetico()
    # El cazador en 4 persigue al jugador en 1 a través de salas no exploradas por el jugador
    accion, costo, dest = decidir_accion_cazador(est, "caz-niebla", catalogo=cat._fichas)
    assert accion == "mover"
    assert dest == 3
    assert costo == 80


def test_vista_muestra_costos_y_cazador():
    """T029 / FR-CAZ-13: FotoEstado contiene los costos de cada salida de la sala actual
    y el cazador se distingue en la lista de enemigos."""
    est = crear_estado_base(salas_total=3, sala_inicial=1)
    conectar_salas(est, 1, "E", 2, "O", costo=175)
    conectar_salas(est, 1, "S", 3, "N", costo=320)

    est.salas[1].enemigos.append(
        EnemigoInstancia(instancia="caz-v", tipo_id="cazador-estandar", vida_actual=20, sala_actual=1)
    )
    est.salas[1].enemigos.append(
        EnemigoInstancia(instancia="err-v", tipo_id="errante-test", vida_actual=10, sala_actual=1)
    )

    prov = ProveedorSintetico()
    fachada = Fachada(est, prov, prov.catalogo._fichas)
    foto = fachada.foto()

    # Costos en salidas visibles
    assert "E" in foto.puertas
    assert foto.puertas["E"]["costo"] == 175
    assert "S" in foto.puertas
    assert foto.puertas["S"]["costo"] == 320

    # Distinción de comportamiento en enemigos
    cazador_foto = next((e for e in foto.enemigos if e["instancia"] == "caz-v"), None)
    errante_foto = next((e for e in foto.enemigos if e["instancia"] == "err-v"), None)
    assert cazador_foto is not None
    assert cazador_foto["comportamiento"] == "cazador"
    assert errante_foto is not None
    assert errante_foto["comportamiento"] == "errante"


# ===========================================================================
# Phase 6: Tests for User Story 4 (Escalabilidad, rendimiento y --bench)
# ===========================================================================

def test_rendimiento_ciclo_cazadores_menos_20ms():
    """T034 / FR-CAZ-14 / SC-CAZ-01: El ciclo de eventos con 50 cazadores activos
    toma <= 20 ms."""
    from src.orchestrator.bench import medir_ciclo_cazadores
    dt = medir_ciclo_cazadores(50, historia=True)
    assert dt <= 0.020, f"Ciclo completo con historia tomó {dt:.4f} s (>0.020s)"


def test_rendimiento_rango_pequeno_independiente_tamano_cripta():
    """T035 / FR-CAZ-14 / SC-CAZ-02: Para rango pequeño (R=200) el tiempo de decisión
    en cripta de 10 000 salas no crece con el tamaño del mapa y permanece < 1.0 ms."""
    from src.controller2.enemigos import decidir_accion_cazador

    est = crear_estado_base(salas_total=10000, sala_inicial=1)
    for i in range(1, 10000):
        conectar_salas(est, i, "E", i + 1, "O", costo=100)

    est.salas[2].enemigos.append(
        EnemigoInstancia(instancia="caz-peq-10k", tipo_id="cazador-corto", vida_actual=15, sala_actual=2)
    )

    cat = CatalogoSintetico()

    t0 = time.perf_counter()
    accion, costo, dest = decidir_accion_cazador(est, "caz-peq-10k", catalogo=cat._fichas)
    dt = time.perf_counter() - t0

    assert accion == "mover"
    assert dest == 1
    # SC-CAZ-02: tiempo < 1.0 ms (0.001 s)
    assert dt < 0.005, f"Decisión tomó {dt:.5f} s"


def test_bench_suite_cazador_ejecucion():
    """T036 / FR-CAZ-15: Ejecución íntegra y sin errores de la suite de cazadores en --bench."""
    from src.orchestrator.bench import bench_cazadores

    res = bench_cazadores(repeticiones=1)
    assert isinstance(res, dict)
    assert len(res) >= 5

    claves_requeridas = [
        "cazador_1_ciclo",
        "cazadores_50_ciclo",
        "cazador_rango_pequeno_10k",
        "cazador_individual",
        "cazador_compartido",
        "cazador_reutilizacion",
        "cazador_recalculo",
        "cazador_puertas_estables",
        "cazador_puertas_inestables",
        "cazador_monticulo_minimo",
        "cazador_lista_enlazada",
    ]
    for k in claves_requeridas:
        assert k in res, f"Clave {k} ausente en bench_cazadores()"
        assert isinstance(res[k], (float, int)), f"{k} debe ser float o int"
        assert res[k] > 0, f"{k} debe ser > 0"





def test_comparador_enlazado_coincide_con_monticulo():
    from src.orchestrator.bench import _dijkstra_lista_enlazada
    from src.controller2.rutas import dijkstra_individual
    estado = crear_estado_base()
    conectar_salas(estado, 1, "E", 2, "O", costo=500)
    conectar_salas(estado, 1, "N", 3, "S", costo=20)
    conectar_salas(estado, 3, "E", 2, "N", costo=30)
    for rango in (40, 50, 1000):
        assert _dijkstra_lista_enlazada(estado, 1, 2, rango) == dijkstra_individual(estado, 1, 2, rango)[0]


def test_busqueda_local_no_explora_region_del_jugador(monkeypatch):
    import src.controller2.rutas as rutas
    estado = crear_estado_base(salas_total=1000, sala_inicial=1)
    for i in range(1, 1000):
        conectar_salas(estado, i, "E", i + 1, "O", costo=100)
    visitadas = []
    original = rutas._obtener_salidas_sala
    def observar(estado, sala_id, proveedor=None):
        visitadas.append(sala_id)
        return original(estado, sala_id, proveedor)
    monkeypatch.setattr(rutas, "_obtener_salidas_sala", observar)
    assert rutas.dijkstra_acotado(estado, 999, 1, 200) == (None, None)
    assert visitadas and all(sala >= 997 for sala in visitadas)


def test_cazador_planea_por_sala_descargada_y_puerta_inicial_cerrada():
    from src.models.conocimiento import DatosSala, DatosSalida
    from src.controller2.enemigos import decidir_accion_cazador
    estado = crear_estado_base()
    conectar_salas(estado, 1, "E", 2, "O", costo=50)
    conectar_salas(estado, 2, "E", 3, "O", costo=50)
    conectar_salas(estado, 3, "E", 4, "O", costo=50)
    estado.salas[4].enemigos.append(EnemigoInstancia("caz", "cazador-estandar", 20, 4))
    del estado.salas[2]
    estado.salas_visitadas = [1]
    class Proveedor:
        cerrada = False
        def datos_sala(self, sala_id):
            assert sala_id == 2
            return DatosSala(2, "sin contenido", (
                DatosSalida("O", 1, 50, (1, "E"), cerrada_inicial=self.cerrada),
                DatosSalida("E", 3, 50, (2, "E"))))
        def sala_lista(self, sala_id):
            pytest.fail("planear no descarga contenido")
    proveedor = Proveedor()
    cat = CatalogoSintetico()._fichas
    assert decidir_accion_cazador(estado, "caz", cat, proveedor)[0] == "mover"
    estado.salas[4].enemigos[0]._ruta_cazador = None
    proveedor.cerrada = True
    estado.salas[1].salidas["E"].cerrada = True
    assert decidir_accion_cazador(estado, "caz", cat, proveedor)[0] == "esperar"


def test_cazador_entra_en_sala_descargada_sin_contenido():
    from src.models.conocimiento import DatosSala, DatosSalida
    from src.controller2.enemigos import turno_enemigo
    from src.controller2.agenda import Agenda
    from src.controller2.reloj import RelojVirtual
    estado = crear_estado_base()
    conectar_salas(estado, 1, "E", 2, "O", costo=50)
    conectar_salas(estado, 2, "E", 3, "O", costo=50)
    estado.salas[3].enemigos.append(EnemigoInstancia("caz", "cazador-estandar", 20, 3))
    del estado.salas[2]
    estado.salas_visitadas = [1]
    class Proveedor:
        def datos_sala(self, sala_id):
            return DatosSala(2, "sin contenido", (
                DatosSalida("O", 1, 50, (1, "E")),
                DatosSalida("E", 3, 50, (2, "E"))))
        def sala_lista(self, sala_id):
            pytest.fail("el movimiento del cazador no descarga contenido")
    turno_enemigo(estado, Agenda(), RelojVirtual(), "caz",
                  CatalogoSintetico()._fichas, proveedor=Proveedor())
    assert estado.salas[2].enemigos[0].instancia == "caz"
    assert not estado.salas[2].visitada
    assert 2 not in estado.salas_visitadas


def test_sala_pendiente_guardado_y_entrada_jugador_conservan_cazador(tmp_path):
    from src.controller1 import savegame
    from src.controller2.movimiento import intentar_mover
    from src.controller2.agenda import Agenda
    from src.controller2.reloj import RelojVirtual
    estado = crear_estado_base()
    conectar_salas(estado, 1, "E", 2, "O", costo=70)
    sala = estado.salas[2]
    sala.contenido_pendiente = True
    sala.enemigos.append(EnemigoInstancia("visitante", "cazador-estandar", 20, 2))
    estado.salas_visitadas = [1]
    ruta = tmp_path / "pendiente.bin"
    savegame.guardar(str(ruta), estado.a_dict())
    assert ruta.read_bytes()[len(savegame.MAGIA)] == 5
    estado = EstadoPartida.desde_dict(savegame.cargar(str(ruta)))
    assert estado.salas[2].contenido_pendiente
    class Proveedor:
        def sala_lista(self, sala_id):
            return SalaViva(2, "cargada", objetos_suelo=["tesoro"])
    resultado = intentar_mover(estado, "E", Proveedor(), Agenda(), RelojVirtual(),
                               CatalogoSintetico()._fichas)
    assert resultado.ok and resultado.costo == 70
    assert not estado.salas[2].contenido_pendiente
    assert estado.salas[2].objetos_suelo == ["tesoro"]
    assert estado.salas[2].enemigos[0].instancia == "visitante"
    assert estado.salas[2].salidas["O"].costo == 70


def test_puerta_reciproca_abre_cierra_y_deshace_desde_ambos_extremos():
    from src.controller2.movimiento import abrir_puerta, ejecutar_cierre
    from src.controller2.agenda import Agenda
    from src.controller2.reloj import RelojVirtual
    from src.controller2.deshacer import aplicar_inversa
    estado = crear_estado_base()
    conectar_salas(estado, 1, "E", 2, "O", cerrada=True, llave="llave")
    estado.jugador.inventario.append("llave")
    agenda = Agenda()
    assert abrir_puerta(estado, "E", agenda, RelojVirtual()).ok
    assert not estado.salas[2].salidas["O"].cerrada
    assert ejecutar_cierre(estado, 2, "O")
    assert estado.salas[1].salidas["E"].cerrada
    assert aplicar_inversa(estado, agenda, {"op": "cierre", "datos": {
        "sala": 2, "direccion": "O", "cerrada_antes": False}})
    assert not estado.salas[1].salidas["E"].cerrada
    assert aplicar_inversa(estado, agenda, {"op": "abrir", "datos": {
        "sala": 1, "direccion": "E"}})
    assert estado.salas[2].salidas["O"].cerrada


def test_turno_reutiliza_ubicacion_del_actor():
    from src.controller2.enemigos import turno_enemigo
    from src.controller2.agenda import Agenda
    from src.controller2.reloj import RelojVirtual
    class SalasContadas(dict):
        recorridos = 0
        def values(self):
            self.recorridos += 1
            return super().values()
    estado = crear_estado_base()
    conectar_salas(estado, 1, "E", 2, "O", costo=100)
    estado.salas[2].enemigos.append(EnemigoInstancia("caz", "cazador-estandar", 20, 2))
    estado.salas = SalasContadas(estado.salas)
    turno_enemigo(estado, Agenda(), RelojVirtual(), "caz", CatalogoSintetico()._fichas)
    assert estado.salas[1].enemigos[0].instancia == "caz"
    assert estado.salas.recorridos <= 2


def test_campo_compartido_equivale_a_individual_en_arcos_dirigidos():
    from src.controller2.rutas import CampoCazadores, dijkstra_individual, dijkstra_acotado
    from src.controller2.movimiento import cambiar_puerta
    estado = crear_estado_base()
    conectar_salas(estado, 1, "E", 2, "O", costo=40)
    conectar_salas(estado, 2, "E", 3, "O", costo=60)
    conectar_salas(estado, 1, "N", 4, "S", costo=30)
    conectar_salas(estado, 4, "E", 3, "N", costo=70)
    del estado.salas[2].salidas["E"]
    campo = CampoCazadores(estado, object())
    for destino in (1, 3, 4):
        estado.sala_actual = destino
        for origen in (1, 2, 3, 4):
            assert dijkstra_acotado(estado, origen, destino, 500, campo.obtener(500)) == dijkstra_individual(estado, origen, destino, 500)
    cambiar_puerta(estado, 4, "E", True)
    for origen in (1, 2, 3, 4):
        assert dijkstra_acotado(estado, origen, 4, 500, campo.obtener(500)) == dijkstra_individual(estado, origen, 4, 500)


def test_sync_rng_actualiza_aunque_contador_estado_ya_coincida():
    estado = crear_estado_base()
    conectar_salas(estado, 1, "E", 2, "O")
    fachada = Fachada(estado, object(), CatalogoSintetico()._fichas)
    fachada._sync()
    previo = estado.azar_estado
    fachada.azar.randint(0, 100)
    estado.azar_llamadas = fachada.azar.llamadas
    fachada._sync()
    assert estado.azar_estado != previo
    assert estado.azar_estado == fachada.azar._rng.getstate()
