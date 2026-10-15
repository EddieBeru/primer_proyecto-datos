"""Compatibilidad: `src.adapters.offline` es `src.controller1.offline` (mismo módulo)."""
import sys as _sys
from src.controller1 import offline as _canon
_sys.modules[__name__] = _canon
