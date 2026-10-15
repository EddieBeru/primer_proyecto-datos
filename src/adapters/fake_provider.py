"""Compatibilidad: `src.adapters.fake_provider` es `src.controller1.fake_provider` (mismo módulo)."""
import sys as _sys
from src.controller1 import fake_provider as _canon
_sys.modules[__name__] = _canon
