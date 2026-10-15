"""Compatibilidad: `src.game.bench` es `src.orchestrator.bench` (mismo módulo)."""
import sys as _sys
from src.orchestrator import bench as _canon
_sys.modules[__name__] = _canon
