"""--bench por subsistema (§5.3 + §4): agenda, caché, disco, inventario,
retroceso, ordenamientos, guardado/carga. Sin red ni vista.

Vive en el orquestador: compone C1 (adapters) y C2 (controller) para medir.
C1 nunca ve C2 y C2 nunca ve C1; quien ve ambos es esta capa.
"""

from __future__ import annotations

import time

from src.controller1.fake_provider import FakeProvider
from src.controller1.unicos import unicos
from src.controller1.lista_doble import ListaDoble, Nodo
from src.controller1.lru_cache import CacheLRU
from src.controller1.mergesort import mergesort
from src.controller1.orden import insertsort, orden_auto
from src.controller2 import Agenda, EstadoPartida, Inventario, PilaDeshacer, RelojVirtual


def _mide(fn, repeticiones: int = 3):
    mejor = None
    for _ in range(max(1, repeticiones)):
        t0 = time.perf_counter()
        fn()
        dt = time.perf_counter() - t0
        mejor = dt if mejor is None else min(mejor, dt)
    return mejor


def bench_agenda(n: int = 500):
    def carga():
        ag = Agenda()
        for i in range(n):
            ag.programar(i % 50, f"ev{i % 7}", {})
        while not ag.vacia:
            ag.sacar_proximo()
    return {"agenda_500": _mide(carga)}


def bench_cache(n: int = 2000):
    c = CacheLRU(25, "v")
    for i in range(25):
        c.guardar(f"k{i}", i)

    def hits():
        for i in range(n):
            c.obtener(f"k{i % 25}")

    def misses():
        for i in range(n):
            c.obtener("no-existe")

    return {"cache_hits_2000": _mide(hits), "cache_misses_2000": _mide(misses)}


def bench_disco(tmpdir=None):
    import os
    import tempfile
    if tmpdir is None:
        tmpdir = tempfile.gettempdir()
    c = CacheLRU(25, "v")
    for i in range(25):
        c.guardar(f"k{i}", {"id": f"k{i}"})
    ruta = os.path.join(tmpdir, "bench_cache.pkl")

    def guarda():
        c.guardar_disco(ruta)

    def carga():
        CacheLRU.cargar_disco(ruta, 25)

    out = {"cache_disco_guarda": _mide(guarda), "cache_disco_carga": _mide(carga)}
    try:
        os.unlink(ruta)
    except OSError:
        pass
    return out


def bench_inventario(n: int = 1000):
    inv = Inventario(100)
    for i in range(100):
        inv.recoger(f"it{i}")

    def recorre():
        list(inv)
        list(reversed(inv))

    def suelta_equipa():
        inv.soltar_en(50)
        inv.recoger("tmp")
        inv.equipar(99)

    return {"inventario_recorre": _mide(recorre), "inventario_suelta_equipar": _mide(suelta_equipa)}


def bench_retroceso(n: int = 200):
    def carga():
        p = PilaDeshacer()
        for i in range(n):
            p.apilar({"op": "equipar", "datos": {"orden_antes": [i]}, "eventos": []})
        while not p.vacia:
            p.desapilar()
    return {"retroceso_200": _mide(carga)}


def bench_ordenamientos():
    import random
    rng = random.Random(7)
    res = {}
    for n in (500, 2000, 8000):
        datos = [rng.randint(0, n) for _ in range(n)]
        t0 = time.perf_counter()
        mergesort(datos)
        res[f"mergesort_{n}"] = time.perf_counter() - t0
        t0 = time.perf_counter()
        orden_auto(datos)
        res[f"orden_auto_{n}"] = time.perf_counter() - t0
    casi = list(range(2000))
    t0 = time.perf_counter()
    insertsort(casi)
    res["insertsort_casi_2000"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    mergesort(casi)
    res["mergesort_casi_2000"] = time.perf_counter() - t0
    return res


def bench_guardado():
    from src.controller1 import savegame
    from src.models.dungeons import DungeonGeneral
    ficha = DungeonGeneral.from_dict({
        "id": "bench", "version": "v", "salas_total": 1, "paginas": 1,
        "salas_por_pagina": 50, "sala_inicial": 1, "sala_salida": 1,
        "llave_salida": "k", "presupuesto_solicitudes": 9, "inventario_max": 10,
        "jugador": {"vida_max": 30, "ataque": 6, "defensa": 2, "velocidad": 100}})
    est = EstadoPartida.nueva_partida(ficha, "cat", semilla=1)
    comp = savegame.comparar_json(est.a_dict())
    return {"guardado_bin_bytes": comp["bin_bytes"], "guardado_json_bytes": comp["json_bytes"],
            "guardado_bin_carga_s": comp["bin_carga_s"], "guardado_json_carga_s": comp["json_carga_s"]}


class _BackendSintetico:
    """Backend forma-endpoints sobre FakeProvider: ciclo completo sin red.

    El bench no puede depender de `paquete_demo/` (fixture de tests): se
    construye aquí el mínimo del protocolo de la Sesión.
    """

    def __init__(self) -> None:
        self.fake = FakeProvider()

    def info_cripta(self, cripta_id, budget=None):
        return self.fake.preparar_cripta(cripta_id)

    def version_catalogo(self, budget=None):
        from src.models.catalog import CatalogVersion
        return CatalogVersion(version="bench-cat-v1")

    def esqueleto_completo(self, cripta_id, budget=None, info=None):
        return dict(self.fake._salas)

    def ubicaciones_llaves(self, cripta_id, budget=None, version_cripta=None):
        return self.fake.ubicaciones_llaves(cripta_id, budget, version_cripta)

    def contenido(self, cripta_id, salas, budget=None):
        from src.models.roomContents import ContenidoResponse
        return ContenidoResponse(contenido=[self.fake._contenido[s] for s in salas])

    def lote_catalogo_auto(self, ids, budget=None):
        return {i: self.fake.ficha(i) for i in unicos(ids)}


def bench_buffer(n: int = 100000):
    """§4.8: la bitácora en pantalla es circular: memoria constante."""
    from src.controller2.buffer_circular import BufferCircular
    b = BufferCircular(20)

    def carga():
        for i in range(n):
            b.agregar(f"m{i}")

    return {"buffer_100k_agrega": _mide(carga), "buffer_largo": len(b)}


def bench_cancelacion(n: int = 20000):
    """§4.1/§8: cancelar por tipo indexado vs barrer toda la agenda."""

    def arma():
        # t creciente (patrón real del reloj): el alta entra por el camino
        # rápido O(1); el costo que se mide es solo el de cancelar.
        ag = Agenda()
        for i in range(n):
            ag.programar(i, "veneno" if i % 50 == 0 else "turno", {})
        return ag

    def cronometra(fn):
        mejor = None
        for _ in range(3):
            ag = arma()
            t0 = time.perf_counter()
            fn(ag)
            dt = time.perf_counter() - t0
            mejor = dt if mejor is None else min(mejor, dt)
        return mejor

    return {
        "agenda_cancelar_tipo_20k": cronometra(lambda ag: ag.cancelar_tipo("veneno")),
        "agenda_cancelar_barrido_20k": cronometra(
            lambda ag: ag.cancelar_donde(lambda e: e.tipo == "veneno")),
    }


def bench_almacen(n: int = 200):
    """§4.4: recuperar una ficha desalojada del almacén en disco es O(1)."""
    import os
    import tempfile
    from src.controller1.almacen_fichas import AlmacenFichas
    ruta = os.path.join(tempfile.gettempdir(), "bench_almacen.fichas")
    try:
        os.unlink(ruta)
    except OSError:
        pass
    alm = AlmacenFichas(ruta=ruta)
    alm.guardar_lote((f"f{i}", {"id": f"f{i}", "cuerpo": "x" * 60}) for i in range(n))

    def recupera():
        for i in range(n):
            alm.obtener(f"f{i}")

    out = {"almacen_recupera_200": _mide(recupera),
           "almacen_carga_disco": _mide(lambda: AlmacenFichas.cargar_disco(ruta))}
    try:
        os.unlink(ruta)
    except OSError:
        pass
    return out


RUTA_VICTORIA = ["s", "recoger llave-hierro-01", "e", "abrir N", "n", "abrir S",
                 "s", "recoger llave-salida-01", "s", "abrir O", "o", "abrir E", "e"]


def bench_ciclo_completo(repeticiones: int = 3):
    """Ciclo de partida de punta a punta sin red ni vista (§5.3).

    Iniciar (esqueleto + sala inicial + vecinas dormidas) y jugar la ruta
    de victoria con caché y almacén en disco reales.
    """
    import os
    import tempfile
    from src.controller1.fake_provider import CRIPTA_ID
    from src.orchestrator.sesion import Sesion
    with tempfile.TemporaryDirectory() as d:
        cache_ruta = os.path.join(d, "bench_cache.pkl")
        pasos = 0

        def ciclo():
            nonlocal pasos
            ses = Sesion(backend=_BackendSintetico(), cache_ruta=cache_ruta,
                         log_ruta=None, puntajes_ruta=os.path.join(d, "p.jsonl"),
                         jugador="bench")
            ses.iniciar(CRIPTA_ID, semilla=1)
            pasos = 0
            for cmd in RUTA_VICTORIA:
                ses.paso(cmd, grabar=False)
                pasos += 1

        t = _mide(ciclo, repeticiones)
        return {"ciclo_completo_s": t, "ciclo_pasos": pasos}


def _crear_cripta_bench(n_salas: int = 100):
    """Crea una cripta en memoria para micro-benchmarks de cazadores."""
    from src.models.dungeons import DungeonGeneral
    from src.controller2.modelo import EstadoPartida, SalaViva, SalidaViva
    ficha = DungeonGeneral.from_dict({
        "id": "cripta-bench",
        "version": "v1",
        "salas_total": n_salas,
        "paginas": 1,
        "salas_por_pagina": n_salas,
        "sala_inicial": 1,
        "sala_salida": n_salas,
        "llave_salida": "llave-salida",
        "presupuesto_solicitudes": 100,
        "inventario_max": 5,
        "jugador": {"vida_max": 30, "ataque": 10, "defensa": 2, "velocidad": 100},
    })
    est = EstadoPartida.nueva_partida(ficha, version_catalogo="cat-bench")
    for i in range(1, n_salas + 1):
        est.registrar_sala(SalaViva(id=i, nombre=f"Sala {i}"))
    for i in range(1, n_salas):
        costo = 50 + (i % 3) * 50
        est.salas[i].salidas["E"] = SalidaViva(direccion="E", destino=i + 1, costo=costo)
        est.salas[i + 1].salidas["O"] = SalidaViva(direccion="O", destino=i, costo=costo)
    return est


def _catalogo_cazadores():
    from src.models.catalog import Enemy
    return {
        "cazador-normal": Enemy(
            id="cazador-normal",
            nombre="Cazador Normal",
            vida_max=20,
            ataque=5,
            defensa=1,
            velocidad=100,
            comportamiento="cazador",
            rango=5000,
        ),
        "cazador-pequeno": Enemy(
            id="cazador-pequeno",
            nombre="Cazador Rango Pequeño",
            vida_max=20,
            ataque=5,
            defensa=1,
            velocidad=100,
            comportamiento="cazador",
            rango=200,
        ),
    }


def _dijkstra_lista_enlazada(estado, origen, destino, rango_max=None):
    from src.estructuras.tabla_indice import TablaIndice
    distancias = TablaIndice()
    distancias[origen] = 0
    cola = ((0, origen), None)
    while cola is not None:
        (d_actual, actual), cola = cola
        if actual == destino:
            break
        if rango_max is not None and d_actual > rango_max:
            continue
        sala = estado.salas.get(actual)
        if not sala:
            continue
        for salida in sala.salidas.values():
            if salida.cerrada:
                continue
            v = salida.destino
            d_tent = d_actual + salida.costo
            if rango_max is not None and d_tent > rango_max:
                continue
            if v not in distancias or d_tent < distancias[v]:
                distancias[v] = d_tent
                # Lista enlazada ordenada: cada nodo contiene valor y siguiente.
                anteriores = []
                while cola is not None and cola[0][0] <= d_tent:
                    anteriores.append(cola[0])
                    cola = cola[1]
                cola = ((d_tent, v), cola)
                while anteriores:
                    cola = (anteriores.pop(), cola)
    return distancias.obtener(destino, None)


def medir_ciclo_cazadores(cantidad=50, salas=1000, historia=True):
    """Medir drenaje real; preparación fuera del reloj, sin red ni render."""
    from time import perf_counter_ns
    from src.controller2.modelo import EnemigoInstancia
    from src.controller2.fachada import Fachada
    from src.orchestrator.sesion import Sesion
    estado = _crear_cripta_bench(salas)
    for i in range(2, cantidad + 2):
        estado.salas[i].enemigos.append(EnemigoInstancia(
            f"caz-{i}", "cazador-normal", 20, i, activa=True))
    fachada = Fachada(estado, object(), _catalogo_cazadores(), oleada_cada=1000000)
    for i in range(2, cantidad + 2):
        fachada.agenda.programar(1, "turno", {"actor": f"caz-{i}", "kind": "enemigo"})
    sesion = Sesion(log_ruta=None)
    sesion.estado, sesion.fachada = estado, fachada
    if historia:
        from src.controller2.linea_tiempo import LineaTiempo
        fachada._sync()
        sesion.linea = LineaTiempo(estado)
        fachada.receptor_historia = sesion.linea
        sesion.linea.comenzar()
    inicio = perf_counter_ns()
    fachada.esperar()
    sesion._drenar()
    if historia:
        sesion.linea.cerrar_accion({"reloj": 0, "tipo": "esperar"}, estado)
    duracion = (perf_counter_ns() - inicio) / 1e9
    if fachada.error is not None:
        raise RuntimeError(fachada.error)
    return duracion


def bench_cazadores(repeticiones: int = 3) -> dict:
    """Suite de evaluación de rendimiento de terreno y cazador (FR-CAZ-14, FR-CAZ-15).
    
    Cubre los 5 ejes obligatorios:
    1. 1 cazador vs. 50 cazadores en ciclo de eventos (SC-CAZ-01).
    2. Rango pequeño (R=200) vs. grande (R=5000) en criptas de 100, 1k y 10k salas (SC-CAZ-02).
    3. Cálculo compartido desde el jugador vs. individual desde cada cazador.
    4. Reutilización de ruta en caché vs. recálculo total continuo.
    5. Puertas estables vs. puertas inestables con invalidación.
    Comparativa de estructuras: MonticuloMinimo vs. lista enlazada ordenada.
    """
    from src.controller2.modelo import EnemigoInstancia
    from src.controller2.rutas import distancias_desde_destino, dijkstra_individual, dijkstra_acotado
    from src.controller2.enemigos import decidir_accion_cazador

    cat = _catalogo_cazadores()

    # Eje 1: 1 vs 50 cazadores (cripta 1000 salas)
    est_1k = _crear_cripta_bench(1000)
    for i in range(2, 52):
        est_1k.salas[i].enemigos.append(
            EnemigoInstancia(instancia=f"caz-{i}", tipo_id="cazador-normal", vida_actual=20, sala_actual=i)
        )

    def ciclo_1():
        decidir_accion_cazador(est_1k, "caz-2", catalogo=cat)

    def ciclo_50():
        dist_comp = distancias_desde_destino(est_1k, destino=1, rango_max=5000)
        for i in range(2, 52):
            decidir_accion_cazador(est_1k, f"caz-{i}", catalogo=cat)

    t_1 = _mide(ciclo_1, repeticiones)
    t_50 = _mide(ciclo_50, repeticiones)

    # Eje 2: Rango pequeño vs rango grande en diferentes tamaños de cripta
    est_100 = _crear_cripta_bench(100)
    est_100.salas[2].enemigos.append(
        EnemigoInstancia(instancia="caz-p100", tipo_id="cazador-pequeno", vida_actual=20, sala_actual=2)
    )
    t_peq_100 = _mide(lambda: decidir_accion_cazador(est_100, "caz-p100", catalogo=cat), repeticiones)

    est_10k = _crear_cripta_bench(10000)
    est_10k.salas[2].enemigos.append(
        EnemigoInstancia(instancia="caz-p10k", tipo_id="cazador-pequeno", vida_actual=20, sala_actual=2)
    )
    t_peq_10k = _mide(lambda: decidir_accion_cazador(est_10k, "caz-p10k", catalogo=cat), repeticiones)

    est_grande_1k = _crear_cripta_bench(1000)
    est_grande_1k.salas[500].enemigos.append(
        EnemigoInstancia(instancia="caz-g1k", tipo_id="cazador-normal", vida_actual=20, sala_actual=500)
    )
    t_grande_1k = _mide(lambda: decidir_accion_cazador(est_grande_1k, "caz-g1k", catalogo=cat), repeticiones)

    # Eje 3: Cálculo individual vs. compartido (50 cazadores en cripta 500)
    est_comp = _crear_cripta_bench(500)
    for i in range(2, 52):
        est_comp.salas[i].enemigos.append(
            EnemigoInstancia(instancia=f"caz-c{i}", tipo_id="cazador-normal", vida_actual=20, sala_actual=i)
        )

    def individual_50():
        for i in range(2, 52):
            dijkstra_individual(est_comp, origen=i, destino=1, rango_max=3000)

    def compartido_50():
        dist_comp = distancias_desde_destino(est_comp, destino=1, rango_max=3000)
        for i in range(2, 52):
            dijkstra_acotado(est_comp, origen=i, destino=1, rango_max=3000, distancias_destino=dist_comp)

    t_individual = _mide(individual_50, repeticiones)
    t_compartido = _mide(compartido_50, repeticiones)

    # Eje 4: Reutilización de ruta vs. recálculo total
    def con_reutilizacion():
        for i in range(2, 52):
            decidir_accion_cazador(est_comp, f"caz-c{i}", catalogo=cat)

    def con_recalculo():
        for i in range(2, 52):
            e = next((x for s in est_comp.salas.values() for x in s.enemigos if x.instancia == f"caz-c{i}"), None)
            if e:
                e._ruta_cazador = None
            decidir_accion_cazador(est_comp, f"caz-c{i}", catalogo=cat)

    t_reutilizacion = _mide(con_reutilizacion, repeticiones)
    t_recalculo = _mide(con_recalculo, repeticiones)

    # Eje 5: Puertas estables vs. inestables
    def puertas_estables():
        for i in range(2, 22):
            decidir_accion_cazador(est_comp, f"caz-c{i}", catalogo=cat)

    def puertas_inestables():
        for i in range(2, 22):
            est_comp.puertas_version += 1
            decidir_accion_cazador(est_comp, f"caz-c{i}", catalogo=cat)

    t_estables = _mide(puertas_estables, repeticiones)
    t_inestables = _mide(puertas_inestables, repeticiones)

    # Comparativa de estructuras: MonticuloMinimo vs Lista Enlazada
    est_500 = _crear_cripta_bench(500)
    t_monticulo = _mide(lambda: dijkstra_individual(est_500, origen=400, destino=1, rango_max=50000), repeticiones)
    t_lista = _mide(lambda: _dijkstra_lista_enlazada(est_500, origen=400, destino=1, rango_max=50000), repeticiones)

    return {
        "cazador_1_drenaje_real": medir_ciclo_cazadores(1),
        "cazadores_50_drenaje_real": medir_ciclo_cazadores(50),
        "cazador_1_ciclo": t_1,
        "cazadores_50_ciclo": t_50,
        "cazador_rango_pequeno_100": t_peq_100,
        "cazador_rango_pequeno_10k": t_peq_10k,
        "cazador_rango_grande_1k": t_grande_1k,
        "cazador_individual": t_individual,
        "cazador_compartido": t_compartido,
        "cazador_reutilizacion": t_reutilizacion,
        "cazador_recalculo": t_recalculo,
        "cazador_puertas_estables": t_estables,
        "cazador_puertas_inestables": t_inestables,
        "cazador_monticulo_minimo": t_monticulo,
        "cazador_lista_enlazada": t_lista,
    }


def correr_todo() -> dict:
    out = {}
    out.update(bench_agenda())
    out.update(bench_cache())
    out.update(bench_disco())
    out.update(bench_inventario())
    out.update(bench_retroceso())
    out.update(bench_ordenamientos())
    out.update(bench_guardado())
    out.update(bench_almacen())
    out.update(bench_buffer())
    out.update(bench_cancelacion())
    out.update(bench_ciclo_completo())
    out.update(bench_cazadores())
    from src.orchestrator.bench_niebla import bench_conocimiento, bench_ir_a
    out.update(bench_conocimiento())
    out.update(bench_ir_a())
    from src.orchestrator.bench_historia import bench_historia
    out.update(bench_historia())
    from src.orchestrator.bench_resolubilidad import correr_bench_resolubilidad
    out["003_resolubilidad"] = correr_bench_resolubilidad()
    return out
