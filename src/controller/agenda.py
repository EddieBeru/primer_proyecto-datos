"""Compatibilidad: `src.controller.agenda` es `src.controller2.agenda` (mismo módulo)."""
import sys as _sys
from src.controller2 import agenda as _canon
_sys.modules[__name__] = _canon
