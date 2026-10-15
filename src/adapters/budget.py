"""Compatibilidad: `src.adapters.budget` es `src.controller1.budget` (mismo módulo)."""
import sys as _sys
from src.controller1 import budget as _canon
_sys.modules[__name__] = _canon
