"""Compatibilidad: `src.api.client` es `src.controller1.client` (mismo módulo)."""
import sys as _sys
from src.controller1 import client as _canon
_sys.modules[__name__] = _canon
