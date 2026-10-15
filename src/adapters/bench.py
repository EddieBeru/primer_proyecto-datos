"""--bench por subsistema (§5.3 + §4): agenda, caché, disco, inventario,
retroceso, ordenamientos, guardado/carga. Sin red ni vista."""

from __future__ import annotations

import time

from src.adapters.lista_doble import ListaDoble, Nodo
from src.adapters.lru_cache import CacheLRU
from src.adapters.mergesort import mergesort
from src.adapters.orden import insertsort, orden_auto
from src.controller import Agenda, EstadoPartida, Inventario, PilaDeshacer, RelojVirtual


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


def bench_disco(tmpdir="/tmp"):
    import os
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
    from src.adapters import savegame
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


def correr_todo() -> dict:
    out = {}
    out.update(bench_agenda())
    out.update(bench_cache())
    out.update(bench_disco())
    out.update(bench_inventario())
    out.update(bench_retroceso())
    out.update(bench_ordenamientos())
    out.update(bench_guardado())
    return out
