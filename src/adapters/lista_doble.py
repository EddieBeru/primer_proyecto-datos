"""Compatibilidad: `src.adapters.lista_doble` es `src.controller1.lista_doble` (mismo módulo)."""
import sys as _sys
from src.controller1 import lista_doble as _canon
_sys.modules[__name__] = _canon
