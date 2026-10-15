"""Compatibilidad: `src.controller.combate` es `src.controller2.combate` (mismo módulo)."""
import sys as _sys
from src.controller2 import combate as _canon
_sys.modules[__name__] = _canon
