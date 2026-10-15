"""Compatibilidad: `src.controller.victoria` es `src.controller2.victoria` (mismo módulo)."""
import sys as _sys
from src.controller2 import victoria as _canon
_sys.modules[__name__] = _canon
