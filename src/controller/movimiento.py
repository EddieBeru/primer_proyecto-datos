"""Compatibilidad: `src.controller.movimiento` es `src.controller2.movimiento` (mismo módulo)."""
import sys as _sys
from src.controller2 import movimiento as _canon
_sys.modules[__name__] = _canon
