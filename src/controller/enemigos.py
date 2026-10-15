"""Compatibilidad: `src.controller.enemigos` es `src.controller2.enemigos` (mismo módulo)."""
import sys as _sys
from src.controller2 import enemigos as _canon
_sys.modules[__name__] = _canon
