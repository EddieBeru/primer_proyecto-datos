"""Compatibilidad: `src.controller.deshacer` es `src.controller2.deshacer` (mismo módulo)."""
import sys as _sys
from src.controller2 import deshacer as _canon
_sys.modules[__name__] = _canon
