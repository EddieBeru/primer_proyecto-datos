"""Sesión de cripta: crea el BudgetAdapter y lo deja listo para los requests.

Flujo:
  1. listar_criptas() va SIN budget (pantalla de selección, pre-contador).
  2. iniciar_cripta(id) pide la ficha cruda con reintento 429, crea el
     BudgetAdapter con presupuesto_solicitudes y descuenta los intentos
     usados en ese bootstrap. Retorna (ficha, budget).
  3. Todo request posterior recibe ese budget como arg.

Regla segura: cada intento HTTP cuesta 1, incluidos reintentos y
consultas de versión.
"""

import time
from collections.abc import Callable

from src.adapters.budget import BudgetAdapter
from src.api import endpoints
from src.models.dungeons import DungeonGeneral
from src.models.errors import RateLimitedError


def iniciar_cripta(
    cripta_id: str,
    max_intentos: int = 3,
    esperar_fn: Callable[[float], None] = time.sleep,
) -> tuple[DungeonGeneral, BudgetAdapter]:
    intentos = 0
    ultimo: RateLimitedError | None = None
    ficha: DungeonGeneral | None = None
    for _ in range(max_intentos):
        intentos += 1
        try:
            ficha = endpoints.info_cripta(cripta_id)
            break
        except RateLimitedError as e:
            ultimo = e
            esperar_fn(max(1, e.reintentar_en))
    if ficha is None:
        assert ultimo is not None
        raise ultimo

    budget = BudgetAdapter(presupuesto=ficha.presupuesto_solicitudes)
    for _ in range(intentos):
        budget.gastar()
    return ficha, budget
