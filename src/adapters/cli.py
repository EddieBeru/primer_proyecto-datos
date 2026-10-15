"""Compatibilidad: `src.adapters.cli` es `src.controller1.cli` (mismo módulo)."""
import sys as _sys
from src.controller1 import cli as _canon
_sys.modules[__name__] = _canon
