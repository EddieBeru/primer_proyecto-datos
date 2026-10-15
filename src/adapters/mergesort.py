"""Compatibilidad: `src.adapters.mergesort` es `src.controller1.mergesort` (mismo módulo)."""
import sys as _sys
from src.controller1 import mergesort as _canon
_sys.modules[__name__] = _canon
