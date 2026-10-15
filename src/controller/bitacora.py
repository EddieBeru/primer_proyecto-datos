"""Compatibilidad: `src.controller.bitacora` es `src.controller2.bitacora` (mismo módulo)."""
import sys as _sys
from src.controller2 import bitacora as _canon
_sys.modules[__name__] = _canon
