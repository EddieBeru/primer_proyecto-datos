"""Genera `paquete_demo/` offline desde FakeProvider (sin red, sin presupuesto).

Uso:  python scripts/exportar_paquete.py [destino]
El paquete sirve para `python -m src.main --offline paquete_demo` y
`--jugar/--vista --offline paquete_demo` (guía §10: no gasta presupuesto).
"""

from __future__ import annotations

import dataclasses
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from src.controller1.fake_provider import CRIPTA_ID, FakeProvider
from src.models.catalog import Trap


def vuelca(dest: pathlib.Path, nombre: str, datos: dict) -> None:
    (dest / nombre).write_text(
        json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")


def main(destino: str = "paquete_demo") -> None:
    dest = pathlib.Path(destino)
    dest.mkdir(parents=True, exist_ok=True)
    fp = FakeProvider()
    general = fp.preparar_cripta(CRIPTA_ID)

    vuelca(dest, "criptas.json",
           {"criptas": [dataclasses.asdict(s)
                        for s in fp.listar_criptas().criptas]})
    vuelca(dest, f"cripta_{CRIPTA_ID}.json", dataclasses.asdict(general))
    vuelca(dest, f"version_cripta_{CRIPTA_ID}.json",
           {"id": CRIPTA_ID, "version": general.version})
    vuelca(dest, f"esqueleto_{CRIPTA_ID}_p1.json",
           {"pagina": 1, "total_paginas": 1,
            "salas": [dataclasses.asdict(r) for r in fp._salas.values()]})
    vuelca(dest, f"contenido_{CRIPTA_ID}.json",
           {"contenido": [dataclasses.asdict(fp._contenido[s])
                          for s in sorted(fp._contenido)]})
    entidades = []
    for ficha in fp._fichas.values():
        d = dataclasses.asdict(ficha)
        if isinstance(ficha, Trap):  # el API usa "daño"; el modelo, "dano"
            d["daño"] = d.pop("dano")
        entidades.append(d)
    vuelca(dest, "catalogo.json", {"entidades": entidades})
    vuelca(dest, "version_catalogo.json", {"version": "fake-cat-v1"})
    print(f"paquete en {dest.resolve()} ({len(entidades)} fichas, "
          f"{len(fp._salas)} salas)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "paquete_demo")
