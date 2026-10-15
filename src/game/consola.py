"""Compatibilidad: `src.game.consola` es `src.orchestrator.consola` (mismo módulo)."""
import sys as _sys
from src.orchestrator import consola as _canon
_sys.modules[__name__] = _canon
