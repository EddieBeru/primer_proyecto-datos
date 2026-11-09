"""Preferencias locales de UI, independientes del guardado de la partida."""

import json
import os
from pathlib import Path


def ruta_preferencias() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "cripta" / "ui.json"


def cargar_preferencias(ruta: Path | None = None) -> dict:
    try:
        datos = json.loads((ruta or ruta_preferencias()).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(datos, dict):
        return {}
    resultado = {}
    tamano = datos.get("tamano")
    if (isinstance(tamano, list) and len(tamano) == 2
            and all(type(n) is int and 480 <= n <= 7680 for n in tamano)):
        resultado["tamano"] = tuple(tamano)
    for clave in ("completa", "ayudas"):
        if type(datos.get(clave)) is bool:
            resultado[clave] = datos[clave]
    return resultado


def guardar_preferencias(datos: dict, ruta: Path | None = None) -> bool:
    ruta = ruta or ruta_preferencias()
    temporal = ruta.with_suffix(".tmp")
    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        temporal.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
        temporal.replace(ruta)
        return True
    except OSError:
        return False
