"""Compatibilidad: `src.adapters.tabla_hash` es `src.controller1.tabla_hash` (mismo módulo)."""
import sys as _sys
from src.controller1 import tabla_hash as _canon
_sys.modules[__name__] = _canon
