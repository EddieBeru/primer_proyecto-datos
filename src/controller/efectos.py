"""Compatibilidad: `src.controller.efectos` es `src.controller2.efectos` (mismo módulo)."""
import sys as _sys
from src.controller2 import efectos as _canon
_sys.modules[__name__] = _canon
