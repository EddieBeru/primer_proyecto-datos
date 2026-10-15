"""Compatibilidad: `src.controller.inventario` es `src.controller2.inventario` (mismo módulo)."""
import sys as _sys
from src.controller2 import inventario as _canon
_sys.modules[__name__] = _canon
