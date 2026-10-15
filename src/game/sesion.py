"""Compatibilidad: `src.game.sesion` es `src.orchestrator.sesion` (mismo módulo)."""
import sys as _sys
from src.orchestrator import sesion as _canon
_sys.modules[__name__] = _canon
