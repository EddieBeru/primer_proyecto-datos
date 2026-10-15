"""Compatibilidad: `src.controller.reloj` es `src.controller2.reloj` (mismo módulo)."""
import sys as _sys
from src.controller2 import reloj as _canon
_sys.modules[__name__] = _canon
