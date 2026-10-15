"""Compatibilidad: `src.adapters.lru_cache` es `src.controller1.lru_cache` (mismo módulo)."""
import sys as _sys
from src.controller1 import lru_cache as _canon
_sys.modules[__name__] = _canon
