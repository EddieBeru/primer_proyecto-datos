"""Compatibilidad: `src.api.endpoints` es `src.controller1.endpoints` (mismo módulo)."""
import sys as _sys
from src.controller1 import endpoints as _canon
_sys.modules[__name__] = _canon
