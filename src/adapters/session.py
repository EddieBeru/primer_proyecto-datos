"""Compatibilidad: `src.adapters.session` es `src.controller1.session` (mismo módulo)."""
import sys as _sys
from src.controller1 import session as _canon
_sys.modules[__name__] = _canon
