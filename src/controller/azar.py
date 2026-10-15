"""Compatibilidad: `src.controller.azar` es `src.controller2.azar` (mismo módulo)."""
import sys as _sys
from src.controller2 import azar as _canon
_sys.modules[__name__] = _canon
