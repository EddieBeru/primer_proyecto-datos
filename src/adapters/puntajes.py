"""Compatibilidad: `src.adapters.puntajes` es `src.controller1.puntajes` (mismo módulo)."""
import sys as _sys
from src.controller1 import puntajes as _canon
_sys.modules[__name__] = _canon
