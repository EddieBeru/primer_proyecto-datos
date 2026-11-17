"""Benchmark reproducible de propagación incremental vs búsqueda repetida."""

import os
import platform
import statistics
import subprocess
import sys
import time
import tracemalloc
from types import SimpleNamespace

from src.algoritmos.resolubilidad import verificar_resolubilidad
from src.estructuras.tabla_indice import TablaIndice, _hash_clave
from src.models.resolubilidad import UbicacionLlave, UbicacionesLlaves
from src.models.rooms import Exit, Room


def _familia(info, plano, ubicaciones, familia, semilla):
    """Ajustes deterministas de casos manteniendo E≤4S."""
    llaves = list(ubicaciones.llaves)
    inicio = plano[info.sala_inicial]
    if familia == "ciclo":
        primera = inicio.salidas["E"]
        llaves[0] = UbicacionLlave(llaves[0].id, primera.sala)
    elif familia == "alternativas":
        primera = llaves[0].id
        destino = max(plano) + 7
        inicio.salidas["N"] = Exit(sala=destino, cerrada=True, llave=primera)
        plano[destino] = Room(destino, "Alternativa")
    elif familia == "pendientes":
        destino_pendiente = max(plano) + 100
        for sala_id in tuple(plano):
            if sala_id == info.sala_salida:
                continue
            origen = plano[sala_id]
            for direccion in ("N", "S", "O"):
                if direccion in origen.salidas:
                    continue
                origen.salidas[direccion] = Exit(sala=destino_pendiente, cerrada=True,
                                                   llave="pendiente")
        plano[destino_pendiente] = Room(destino_pendiente, "Pendiente")
        llaves.append(UbicacionLlave("pendiente", info.sala_salida))
    elif familia == "desconexion":
        destino = max(plano) + 7
        plano[destino] = Room(destino, f"Aislada {semilla}")
    return UbicacionesLlaves(info.id, info.version, True, tuple(llaves))


def generar_cadena(n, semilla=300316):
    """Cadena con una llave en cada sala y puerta final requerida."""
    if type(n) is not int or n < 1:
        raise ValueError("n debe ser positivo")
    desplazamiento = semilla % 997 + 1000
    salas = []
    llaves = []
    for i in range(n + 1):
        sid = desplazamiento + i * 7
        if i < n:
            kid = f"llave-{semilla}-{i}"
            salida = Exit(sala=sid + 7, cerrada=True, llave=kid)
        else:
            kid = f"llave-final-{semilla}"
            salida = Exit(sala=sid + 7, cerrada=True, llave=kid)
        salas.append(Room(sid, f"Sala {i}", {"E": salida}))
        llaves.append(UbicacionLlave(kid, sid))
    salida_id = desplazamiento + (n + 1) * 7
    salas.append(Room(salida_id, "Salida"))
    info = SimpleNamespace(id=f"bench-{semilla}-{n}", version="sintetica-v1",
        sala_inicial=desplazamiento, sala_salida=salida_id,
        llave_salida=f"llave-final-{semilla}")
    ubicaciones = UbicacionesLlaves(info.id, info.version, True, tuple(llaves))
    return info, {s.id: s for s in salas}, ubicaciones


def referencia_repetida(info, plano, ubicaciones):
    """Referencia lenta: vuelve a recorrer el plano para cada llave candidata."""
    obtenidas = []
    while True:
        antes = len(obtenidas)
        for candidata in ubicaciones.llaves:
            if candidata.id in obtenidas:
                continue
            cola = [info.sala_inicial]
            cursor = 0
            alcanzables = []
            while cursor < len(cola):
                sala_id = cola[cursor]
                cursor += 1
                if sala_id in alcanzables:
                    continue
                alcanzables.append(sala_id)
                sala = plano[sala_id]
                for direccion in ("N", "S", "E", "O"):
                    salida = sala.salidas.get(direccion)
                    if salida is None:
                        continue
                    if not salida.cerrada_inicial or salida.llave in obtenidas:
                        if salida.sala not in alcanzables:
                            cola.append(salida.sala)
            if any(u.id == candidata.id and u.sala in alcanzables
                   for u in ubicaciones.llaves):
                obtenidas.append(candidata.id)
        if len(obtenidas) == antes:
            break
    cola = [info.sala_inicial]
    cursor = 0
    alcanzables = []
    while cursor < len(cola):
        sala_id = cola[cursor]
        cursor += 1
        if sala_id in alcanzables:
            continue
        alcanzables.append(sala_id)
        for direccion in ("N", "S", "E", "O"):
            salida = plano[sala_id].salidas.get(direccion)
            if salida is not None and (not salida.cerrada_inicial or salida.llave in obtenidas):
                if salida.sala not in alcanzables:
                    cola.append(salida.sala)
    acceso = False
    for sid in alcanzables:
        for salida in plano[sid].salidas.values():
            if salida.sala == info.sala_salida and salida.llave == info.llave_salida:
                acceso = True
    estado = "resoluble" if info.llave_salida in obtenidas and acceso else "no_resoluble"
    return estado, tuple(obtenidas)


def _muestras(fn, repeticiones=7):
    muestras = []
    for _ in range(repeticiones):
        inicio = time.perf_counter_ns()
        fn()
        muestras.append(time.perf_counter_ns() - inicio)
    return muestras


def _colisiones_ids(ids):
    indice = TablaIndice()
    for texto in ids:
        indice[texto] = True
    ocupacion = [0] * indice.capacidad
    for texto in ids:
        ocupacion[_hash_clave(texto) & (indice.capacidad - 1)] += 1
    maximo = max(ocupacion, default=0)
    return indice.capacidad, sum(max(0, n - 1) for n in ocupacion), maximo


def _modelo_cpu():
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as archivo:
            for linea in archivo:
                if linea.lower().startswith(("model name", "hardware")):
                    return linea.split(":", 1)[-1].strip()
    except OSError:
        pass
    return platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER", "desconocida")


def correr_bench_resolubilidad(tamanos=(128, 512, 2048, 8192),
                               familias=("cadena", "ciclo", "pendientes",
                                         "alternativas", "desconexion"),
                               semilla=300316):
    """Muestras totales; generación fuera de reloj, memoria en una ejecución aparte."""
    resultados = []
    for familia in familias:
        for n in tamanos:
            info, plano, ubicaciones = generar_cadena(n, semilla)
            ubicaciones = _familia(info, plano, ubicaciones, familia, semilla)
            verificador = lambda: verificar_resolubilidad(info, plano, ubicaciones, medir=True)
            def fn():
                resultado_local = verificador()
                from src.orchestrator.reporte_resolubilidad import texto_reporte
                texto_reporte(resultado_local)
                return resultado_local
            fn(); fn()  # dos calentamientos requeridos
            muestras = _muestras(fn, 7)
            muestras_algoritmo = _muestras(verificador, 7)
            resultado = verificador()
            from src.orchestrator.reporte_resolubilidad import texto_reporte
            muestras_texto = _muestras(lambda: texto_reporte(resultado), 7)
            tracemalloc.start()
            fn()
            _, memoria = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            comparar = None
            if n <= 512 and familia == "cadena":
                lenta = _muestras(lambda: referencia_repetida(info, plano, ubicaciones), 7)
                comparar = {"muestras_ns": lenta,
                    "mediana_ns": int(statistics.median(lenta)),
                    "maximo_ns": max(lenta)}
            reporte = texto_reporte(resultado)
            capacidad_ids, colisiones_ids, cubeta_maxima_ids = _colisiones_ids(
                [ubic.id for ubic in ubicaciones.llaves])
            resultados.append({"familia": familia, "semilla": semilla, "salas": len(plano),
                "salidas": sum(len(s.salidas) for s in plano.values()),
                "llaves": len(ubicaciones.llaves), "ubicaciones": len(ubicaciones.llaves),
                "bytes_ids": sum(len(x.id.encode("utf-8")) for x in ubicaciones.llaves),
                "capacidad_indice_ids": capacidad_ids,
                "colisiones_ids": colisiones_ids,
                "maximo_ids_por_cubeta": cubeta_maxima_ids,
                "estado": resultado.estado, "orden_valido": len(resultado.orden_llaves),
                "visitas": dict(resultado.contadores), "fases_ns": dict(resultado.tiempos_ns),
                "muestras_total_local_ns": muestras,
                "muestras_algoritmo_ns": muestras_algoritmo,
                "muestras_texto_ns": muestras_texto,
                "mediana_ns": int(statistics.median(muestras)), "maximo_ns": max(muestras),
                "memoria_max_bytes": memoria, "bytes_reporte": len(reporte.encode("utf-8")),
                "comparador_repetido": comparar})
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
            check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        commit = "desconocido"
    return {"capacidad": "003-resolubilidad", "semilla": semilla,
        "interprete": sys.version, "plataforma": platform.platform(),
        "cpu": _modelo_cpu(),
        "commit": commit, "repeticiones": 7, "calentamientos": 2,
        "muestras": resultados}
