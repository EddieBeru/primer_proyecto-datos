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
                 "s", "s", "o", "recoger llave-salida-01", "abrir E", "e"]


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
    return out
