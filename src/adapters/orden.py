"""Compatibilidad: `src.adapters.orden` es `src.controller1.orden` (mismo módulo)."""
import sys as _sys
from src.controller1 import orden as _canon
_sys.modules[__name__] = _canon
