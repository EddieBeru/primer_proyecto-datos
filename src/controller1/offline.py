"""Modo --offline (§3.4 doc oficial).

Lee un paquete de respuestas previamente descargadas desde disco a través
del mismo contrato lógico que el cliente de red. El modelo no distingue
HTTP de archivos. No consume presupuesto (no es red).

Estructura del paquete (dir):
  criptas.json
  cripta_<id>.json
  version_cripta_<id>.json
  esqueleto_<id>_p<pagina>.json
  contenido_<id>_<s1-s2-...>.json   (o contenido_<id>.json con todo)
  catalogo.json                      (dict id -> ficha)
  version_catalogo.json
"""

from __future__ import annotations

import json
import os

from src.models.catalog import CatalogVersion, CatalogoResponse
from src.models.dungeons import CriptasResponse, DungeonGeneral, DungeonVersion
from src.models.errors import NotFoundError
from src.models.roomContents import ContenidoResponse
from src.models.rooms import SkeletonPage
from src.controller1.unicos import unicos


def _leer_json(ruta: str):
    if not os.path.isfile(ruta):
        raise NotFoundError(f"paquete offline sin {ruta}")
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


class OfflineBackend:
    """Mismo contrato funcional que src.controller1.endpoints (solo lectura)."""

    def __init__(self, directorio: str):
        self.dir = directorio

    def _ruta(self, nombre: str) -> str:
        return os.path.join(self.dir, nombre)

    def listar_criptas(self, budget=None) -> CriptasResponse:
        return CriptasResponse.from_dict(_leer_json(self._ruta("criptas.json")))

    def info_cripta(self, cripta_id: str, budget=None) -> DungeonGeneral:
        return DungeonGeneral.from_dict(
            _leer_json(self._ruta(f"cripta_{cripta_id}.json")))

    def version_cripta(self, cripta_id: str, budget=None) -> DungeonVersion:
        return DungeonVersion.from_dict(
            _leer_json(self._ruta(f"version_cripta_{cripta_id}.json")))

    def esqueleto(self, cripta_id: str, pagina: int = 1, budget=None) -> SkeletonPage:
        return SkeletonPage.from_dict(
            _leer_json(self._ruta(f"esqueleto_{cripta_id}_p{pagina}.json")))

    def esqueleto_completo(self, cripta_id: str, budget=None, info=None):
        info = info or self.info_cripta(cripta_id)
        plano = {}
        for pagina in range(1, info.paginas + 1):
            lote = self.esqueleto(cripta_id, pagina)
            for sala in lote.salas:
                plano[sala.id] = sala
        return plano

    def contenido(self, cripta_id: str, salas, budget=None) -> ContenidoResponse:
        lote = list(salas)
        qs = "-".join(map(str, lote))
        cand = self._ruta(f"contenido_{cripta_id}_{qs}.json")
        if os.path.isfile(cand):
            return ContenidoResponse.from_dict(_leer_json(cand))
        todo = _leer_json(self._ruta(f"contenido_{cripta_id}.json"))
        entradas = todo.get("contenido", [])
        sel = []
        for sala in lote:
            for e in entradas:
                if e["sala"] == sala:
                    sel.append(e)
                    break
            else:
                raise NotFoundError(f"offline sin contenido de la sala {sala}")
        return ContenidoResponse.from_dict({"contenido": sel})

    def version_catalogo(self, budget=None) -> CatalogVersion:
        return CatalogVersion.from_dict(_leer_json(self._ruta("version_catalogo.json")))

    def lote_catalogo(self, ids, budget=None) -> CatalogoResponse:
        cat = _leer_json(self._ruta("catalogo.json"))
        fichas = cat.get("entidades", cat) if isinstance(cat, dict) else cat
        if isinstance(fichas, dict):
            sel = [fichas[i] for i in ids if i in fichas]
        else:
            sel = []
            for i in ids:
                for e in fichas:
                    if e["id"] == i:
                        sel.append(e)
                        break
        if len(sel) != len(list(ids)):
            raise NotFoundError("offline sin alguna ficha del lote")
        return CatalogoResponse.from_dict({"entidades": sel})

    def lote_catalogo_auto(self, ids, budget=None):
        ids_unicos = unicos(ids)
        out = {}
        for i in range(0, len(ids_unicos), 10):
            lote = self.lote_catalogo(ids_unicos[i:i + 10])
            for e in lote.entidades:
                out[e.id] = e
        return out

    def ficha_catalogo(self, entidad_id: str, budget=None):
        return self.lote_catalogo([entidad_id])[0]
