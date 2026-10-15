"""Tabla local de puntajes (§2.12 doc oficial). JSONL append, sin binario."""

from __future__ import annotations

import json
import os


def registrar(ruta: str, entrada: dict) -> None:
    with open(ruta, "a", encoding="utf-8") as f:
        f.write(json.dumps(entrada, ensure_ascii=False) + "\n")


def leer_todos(ruta: str) -> list[dict]:
    if not os.path.isfile(ruta):
        return []
    out = []
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if linea:
                out.append(json.loads(linea))
    return out
