"""Compatibilidad: `src.controller.modelo` es `src.controller2.modelo` (mismo módulo)."""
import sys as _sys
from src.controller2 import modelo as _canon
_sys.modules[__name__] = _canon
