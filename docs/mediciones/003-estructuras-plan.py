"""Microbenchmark de alternativas para el diseño003, no del verificador.

Ejecutar desde cualquier directorio con el Python del proyecto. El resultado
se escribe junto al script. Los diccionarios solo serializan el informe JSON;
no se usan como índices ni para resolver las cargas medidas.
"""

from __future__ import annotations

import json
import platform
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.estructuras.tabla_indice import TablaIndice

SEED = 300316
REPETITIONS = 7
WARMUPS = 2


class Nodo:
    __slots__ = ("valor", "siguiente")

    def __init__(self, valor):
        self.valor = valor
        self.siguiente = None


class TablaIndiceTextoPrototipo(TablaIndice):
    """Experimento de extensión neutral, fuera del código de producción.

    Hereda crecimiento, encadenamiento y comparación exacta de claves. FNV1a64
    limita el acumulador por byte; evita enteros crecientes según largo de id.
    """

    def _indice(self, clave):
        if type(clave) is not str:
            return super()._indice(clave)
        h = 14695981039346656037
        for byte in clave.encode("utf-8"):
            h = ((h ^ byte) * 1099511628211) & ((1 << 64) - 1)
        return h & (self.capacidad - 1)


def fifo_cabeza(values):
    pending = []
    for value in values:
        pending.append(value)
    head = 0
    checksum = 0
    while head < len(pending):
        checksum += pending[head]
        head += 1
    return checksum


def fifo_pop_cero(values):
    pending = []
    for value in values:
        pending.append(value)
    checksum = 0
    while pending:
        checksum += pending.pop(0)
    return checksum


def fifo_enlazada(values):
    first = last = None
    for value in values:
        node = Nodo(value)
        if last is None:
            first = node
        else:
            last.siguiente = node
        last = node
    checksum = 0
    while first is not None:
        checksum += first.valor
        first = first.siguiente
    return checksum


def buscar_indice(values):
    index = TablaIndice()
    for position, value in enumerate(values):
        index[value] = position
    checksum = 0
    for value in values:
        checksum += index[value]
    return checksum


def buscar_lineal(values):
    entries = []
    for position, value in enumerate(values):
        entries.append((value, position))
    checksum = 0
    for value in values:
        for key, position in entries:
            if key == value:
                checksum += position
                break
    return checksum


def clave_textual_entera(value):
    # Prefijo no nulo: preserva longitud y ceros iniciales del UTF8.
    return int.from_bytes(b"\x01" + value.encode("utf-8"), "big")


def buscar_texto_indice(values):
    index = TablaIndice()
    for position, value in enumerate(values):
        index[clave_textual_entera(value)] = position
    checksum = 0
    for value in values:
        checksum += index[clave_textual_entera(value)]
    return checksum


def buscar_texto_hash_lineal(values):
    index = TablaIndiceTextoPrototipo()
    for position, value in enumerate(values):
        index[value] = position
    checksum = 0
    for value in values:
        checksum += index[value]
    return checksum


def pertenencia_marcas(values):
    present = [False] * len(values)
    for value in values:
        present[value] = True
    checksum = 0
    for value in values:
        if present[value]:
            checksum += value
    return checksum


def insertion_order(values):
    result = list(values)
    for i in range(1, len(result)):
        item = result[i]
        j = i
        while j > 0 and result[j - 1] > item:
            result[j] = result[j - 1]
            j -= 1
        result[j] = item
    return result


def measure(name, function, values):
    expected = len(values) * (len(values) - 1) // 2
    for _ in range(WARMUPS):
        assert function(values) == expected
    elapsed = []
    for _ in range(REPETITIONS):
        start = time.perf_counter_ns()
        actual = function(values)
        elapsed.append((time.perf_counter_ns() - start) / 1_000_000)
        assert actual == expected
    ordered = insertion_order(elapsed)
    return {"alternative": name, "n": len(values), "samples_ms": elapsed,
            "median_ms": ordered[len(ordered) // 2], "min_ms": ordered[0],
            "max_ms": ordered[-1], "checksum": expected}


def main():
    results = []
    rng = random.Random(SEED)
    for n in (1000, 4000, 16000, 32000):
        values = list(range(n))
        rng.shuffle(values)
        for name, function in (("fifo_lista_cabeza", fifo_cabeza),
                               ("fifo_pop_cero", fifo_pop_cero),
                               ("fifo_enlazada", fifo_enlazada),
                               ("pertenencia_marcas_densas", pertenencia_marcas)):
            results.append(measure(name, function, values))
    for n in (1000, 4000):
        values = list(range(n))
        rng.shuffle(values)
        results.append(measure("indice_propio_entero", buscar_indice, values))
        results.append(measure("busqueda_lineal", buscar_lineal, values))
        textual_values = [f"itm_llave_{value:06d}" for value in values]
        for name, function in (("indice_propio_texto_codificado", buscar_texto_indice),
                               ("indice_propio_texto_fnv1a64", buscar_texto_hash_lineal),
                               ("busqueda_lineal_texto", buscar_lineal)):
            row = measure(name, function, textual_values)
            row["id_max_chars"] = max(len(value) for value in textual_values)
            row["includes"] = "conversión UTF8→entero, construcción y consulta" if function is buscar_texto_indice else "construcción y consulta"
            results.append(row)
    long_values = ["x" * 240 + f"itm_llave_{value:06d}" for value in values]
    for name, function in (("indice_propio_texto_codificado_largo", buscar_texto_indice),
                           ("indice_propio_texto_fnv1a64_largo", buscar_texto_hash_lineal)):
        row = measure(name, function, long_values)
        row["id_max_chars"] = max(len(value) for value in long_values)
        row["includes"] = "construcción y consulta, incluyendo codificación/hash"
        results.append(row)
    report = {
        "scope": "Microbenchmark de estructuras: construcción y consumo/consultas; no mide resolubilidad ni200ms.",
        "python": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "seed": SEED,
        "warmups": WARMUPS,
        "repetitions": REPETITIONS,
        "clock": "time.perf_counter_ns",
        "limitations": [
            "Una ejecución local; resultados sensibles a carga y recolector.",
            "Las marcas densas requieren ordinales compactos, nunca max(id).",
            "Texto medido con ids ASCII de16 y256 caracteres; el prototipo FNV1a64 procesa bytes con acumulador64 bits. No se presupone costo constante para longitudes ilimitadas.",
            "La variante texto→entero es una alternativa descartable: _hash_entero desplaza enteros largos y su costo en bytes puede ser cuadrático; no se presenta como diseño lineal en bytes.",
            "No acredita complejidad del diagnóstico de ciclos ni meta temporal en cripta publicada.",
        ],
        "results": results,
    }
    destination = Path(__file__).with_suffix(".json")
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    for row in results:
        print(f"{row['alternative']} n={row['n']}: mediana={row['median_ms']:.3f}ms max={row['max_ms']:.3f}ms")


if __name__ == "__main__":
    main()
