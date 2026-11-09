import json

import pytest

from config.preferencias import cargar_preferencias, guardar_preferencias, ruta_preferencias


def test_preferencias_roundtrip_aislado_del_guardado(tmp_path):
    ruta = tmp_path / "config" / "cripta" / "ui.json"
    datos = {"tamano": (1600, 900), "completa": True, "ayudas": False}
    assert cargar_preferencias(ruta) == {}
    assert guardar_preferencias(datos, ruta)
    assert cargar_preferencias(ruta) == datos
    assert not ruta.with_suffix(".tmp").exists()


@pytest.mark.parametrize("contenido", ["{", "null", "[]", "23", '"texto"'])
def test_config_corrupta_recupera_defaults(tmp_path, contenido):
    ruta = tmp_path / "ui.json"
    ruta.write_text(contenido)
    assert cargar_preferencias(ruta) == {}


def test_config_valida_tipos_y_dimensiones(tmp_path):
    ruta = tmp_path / "ui.json"
    ruta.write_text(json.dumps({"tamano": [-1, "900"], "completa": "false", "ayudas": False}))
    assert cargar_preferencias(ruta) == {"ayudas": False}


def test_guardado_sin_permiso_no_rompe_salida(tmp_path):
    bloqueo = tmp_path / "archivo"
    bloqueo.write_text("no es un directorio")
    assert not guardar_preferencias({}, bloqueo / "ui.json")


def test_config_respeta_xdg(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert ruta_preferencias() == tmp_path / "cripta" / "ui.json"
