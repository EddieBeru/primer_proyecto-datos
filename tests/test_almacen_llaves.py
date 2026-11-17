"""Persistencia local versionada y escritura atómica de ubicaciones."""

import json
import pytest
from src.models.errors import NotFoundError

from src.controller1.almacen_llaves import AlmacenLlaves
from src.controller1.offline import OfflineBackend
from src.models.resolubilidad import UbicacionLlave, UbicacionesLlaves


def test_cache_por_version_y_offline_sin_red(tmp_path):
    ruta = tmp_path / "llaves_c.json"
    dto = UbicacionesLlaves("c", "v1", True, (UbicacionLlave("k", 9),))
    AlmacenLlaves(str(ruta)).guardar(dto)
    assert AlmacenLlaves(str(ruta)).obtener("c", "v1") == dto
    assert AlmacenLlaves(str(ruta)).obtener("c", "v2") is None
    offline = OfflineBackend(str(tmp_path))
    assert offline.ubicaciones_llaves("c", version_cripta="v1").llaves == dto.llaves


def test_formato_obsoleto_o_corrupto_no_se_usa(tmp_path):
    ruta = tmp_path / "llaves.json"
    ruta.write_text(json.dumps({"formato": 2, "cripta_id": "c",
        "version_cripta": "v", "completa": True, "llaves": []}), encoding="utf-8")
    assert AlmacenLlaves(str(ruta)).obtener("c", "v") is None
    ruta.write_text("{ roto", encoding="utf-8")
    assert AlmacenLlaves(str(ruta)).obtener("c", "v") is None


def test_paquete_offline_antiguo_sin_archivo_falla_sin_red(tmp_path):
    with pytest.raises(NotFoundError):
        OfflineBackend(str(tmp_path)).ubicaciones_llaves("sin-archivo", version_cripta="v")
