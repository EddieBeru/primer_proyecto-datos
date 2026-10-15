"""Sesión de cripta (§5.1 doc oficial).

Toda solicitud HTTP cuenta, incluyendo lista de criptas. Como el presupuesto
solo se conoce tras la ficha, la lista previa se descuenta retroactivamente
al crear el budget en iniciar_cripta (+1 por listar + intentos bootstrap).
"""

import time
from collections.abc import Callable

from src.adapters.budget import BudgetAdapter
from src.api import endpoints
from src.models.dungeons import DungeonGeneral
from src.models.errors import RateLimitedError


def listar_criptas(budget=None):
    """Lista criptas. Si hay budget, cuenta como solicitud (§5.1)."""
    return endpoints.listar_criptas(budget)


def iniciar_cripta(
    cripta_id: str,
    max_intentos: int = 3,
    esperar_fn: Callable[[float], None] = time.sleep,
    contar_lista: bool = True,
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
    if contar_lista:
        try:
            budget.gastar()  # la lista previa de esta partida también cuenta
        except Exception:
            pass
    return ficha, budget
