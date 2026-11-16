"""Audita el flujo puro/preparador de003 contra restricciones estructurales."""

import ast
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
ARCHIVOS = (
    "src/algoritmos/resolubilidad.py",
    "src/models/resolubilidad.py",
    "src/models/rooms.py",
    "src/models/conocimiento.py",
    "src/estructuras/tabla_indice.py",
    "src/estructuras/cola_fifo.py",
    "src/controller1/endpoints.py",
    "src/controller1/offline.py",
    "src/controller1/almacen_llaves.py",
    "src/orchestrator/reporte_resolubilidad.py",
    "src/orchestrator/bench_resolubilidad.py",
    "src/orchestrator/bench.py",
    "src/orchestrator/sesion.py",
    "src/controller1/session.py",
    "src/controller1/cli.py",
    "src/main.py",
    "src/view/app.py",
    "src/view/pantallas.py",
    "tests/fixtures_resolubilidad.py",
    "tests/test_almacen_llaves.py",
    "tests/test_bench_resolubilidad.py",
    "tests/test_cli_resolubilidad.py",
    "tests/test_cola_fifo.py",
    "tests/test_llaves.py",
    "tests/test_resolubilidad.py",
    "tests/test_sesion_resolubilidad.py",
    "tests/test_vista_resolubilidad.py",
)
PROHIBIDOS = ("heapq", "deque", "set", "frozenset")


def test_flujo_no_importa_estructuras_prohibidas_ni_crea_comprehensions_de_set():
    for ruta in ARCHIVOS:
        arbol = ast.parse((RAIZ / ruta).read_text(encoding="utf-8"), filename=ruta)
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Import):
                assert all(alias.name.split(".")[0] not in PROHIBIDOS
                           for alias in nodo.names), ruta
            elif isinstance(nodo, ast.ImportFrom):
                assert nodo.module not in PROHIBIDOS, ruta
                assert all(alias.name not in PROHIBIDOS for alias in nodo.names), ruta
            elif isinstance(nodo, ast.Name):
                assert nodo.id not in PROHIBIDOS, (ruta, nodo.id)
            elif isinstance(nodo, (ast.Set, ast.SetComp, ast.DictComp)):
                assert not isinstance(nodo, (ast.Set, ast.SetComp)), ruta
            elif isinstance(nodo, ast.Call):
                assert not (isinstance(nodo.func, ast.Name) and nodo.func.id == "sorted"), ruta
                assert not (isinstance(nodo.func, ast.Attribute) and nodo.func.attr == "sort"), ruta
                if isinstance(nodo.func, ast.Attribute) and nodo.func.attr == "pop":
                    assert not nodo.args or not (isinstance(nodo.args[0], ast.Constant)
                                                  and nodo.args[0].value == 0), ruta
