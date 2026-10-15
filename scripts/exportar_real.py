"""Vuelca una cripta REAL a paquete offline (un gasto, juego infinito gratis).

Uso:
  python scripts/exportar_real.py cripta-01 [destino]

Gasta presupuesto una sola vez (lista(info)+versiones+esqueleto+contenidos
+catálogo) y deja un dir compatible con OfflineBackend (--offline).
Después: python -m src.main --jugar --offline <destino> sin gastar red.
"""

from __future__ import annotations

import dataclasses
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from src.controller1.budget import BudgetAdapter
from src.models.catalog import Trap


def vuelca(dest: pathlib.Path, nombre: str, datos: dict) -> None:
    (dest / nombre).write_text(
        json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")


def main(cripta_id: str, destino: str | None = None) -> None:
    from src.controller1 import endpoints

    dest = pathlib.Path(destino or f"paquete_{cripta_id}")
    dest.mkdir(parents=True, exist_ok=True)
    budget = BudgetAdapter(presupuesto=10_000)

    criptas = endpoints.listar_criptas(budget)
    vuelca(dest, "criptas.json",
            {"criptas": [dataclasses.asdict(c) for c in criptas.criptas]})
    info = endpoints.info_cripta(cripta_id, budget)
    vuelca(dest, f"cripta_{cripta_id}.json", dataclasses.asdict(info))
    ver_c = endpoints.version_cripta(cripta_id, budget)
    vuelca(dest, f"version_cripta_{cripta_id}.json", dataclasses.asdict(ver_c))
    ver_k = endpoints.version_catalogo(budget)
    vuelca(dest, "version_catalogo.json", dataclasses.asdict(ver_k))

    plano = endpoints.esqueleto_completo(cripta_id, budget, info=info)
    # Reparte páginas según salas_por_pagina de la ficha.
    spp = max(1, info.salas_por_pagina)
    ids = sorted(plano)
    for pagina in range(1, info.paginas + 1):
        lote = ids[(pagina - 1) * spp:pagina * spp]
        vuelca(dest, f"esqueleto_{cripta_id}_p{pagina}.json",
                {"pagina": pagina, "total_paginas": info.paginas,
                 "salas": [dataclasses.asdict(plano[i]) for i in lote]})

    # Contenido completo en lotes de 10 (una petición por lote).
    todo: list = []
    for i in range(0, len(ids), 10):
        resp = endpoints.contenido(cripta_id, ids[i:i + 10], budget)
        todo.extend(dataclasses.asdict(e) for e in resp.contenido)
    vuelca(dest, f"contenido_{cripta_id}.json", {"contenido": todo})

    # Catálogo: tipos vistos + sueltas hasta cierre.
    tipos: list[str] = []
    for e in todo:
        tipos += [x["tipo"] for x in e.get("enemigos", [])]
        tipos += [x["tipo"] for x in e.get("trampas", [])]
        tipos += list(e.get("objetos", []))
    tipos = list(dict.fromkeys(tipos))
    fichas: dict = {}
    pendientes = list(tipos)
    while pendientes:
        lote = [t for t in dict.fromkeys(pendientes[:50]) if t not in fichas]
        pendientes = pendientes[50:]
        for i in range(0, len(lote), 10):
            resp = endpoints.lote_catalogo(lote[i:i + 10], budget)
            for ent in resp.entidades:
                fichas[ent.id] = ent
                for drop in (getattr(ent, "suelta", None) or []):
                    if drop not in fichas and drop not in pendientes:
                        pendientes.append(drop)
    entidades = []
    for f in fichas.values():
        d = dataclasses.asdict(f)
        if isinstance(f, Trap):
            d["daño"] = d.pop("dano")
        entidades.append(d)
    vuelca(dest, "catalogo.json", {"entidades": entidades})
    rep = budget.reporte()
    print(f"paquete en {dest.resolve()} ({len(ids)} salas, {len(entidades)} fichas, "
          f"{rep['realizadas']} solicitudes gastadas una sola vez)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("uso: exportar_real.py CRIPTA_ID [destino]")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
