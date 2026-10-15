"""Compatibilidad: `src.adapters.gamelog` es `src.controller1.gamelog` (mismo módulo)."""
import sys as _sys
from src.controller1 import gamelog as _canon
_sys.modules[__name__] = _canon
