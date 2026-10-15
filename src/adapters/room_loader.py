"""Compatibilidad: `src.adapters.room_loader` es `src.controller1.room_loader` (mismo módulo)."""
import sys as _sys
from src.controller1 import room_loader as _canon
_sys.modules[__name__] = _canon
