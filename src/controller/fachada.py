"""Compatibilidad: `src.controller.fachada` es `src.controller2.fachada` (mismo módulo)."""
import sys as _sys
from src.controller2 import fachada as _canon
_sys.modules[__name__] = _canon
