"""C1-10: CLI parsea banderas y valida, sin red ni archivos."""

import pytest

from src.adapters.cli import CLIConfig, parse_args


def test_defaults():
    cfg = parse_args([])
    assert cfg == CLIConfig(cache_size=50, replay=None, bench=False)


def test_banderas():
    cfg = parse_args(["--cache-size", "20", "--replay", "juego.log", "--bench"])
    assert cfg.cache_size == 20
    assert cfg.replay == "juego.log"
    assert cfg.bench is True


def test_cache_size_invalido():
    for malo in ("0", "-3"):
        with pytest.raises(SystemExit):
            parse_args(["--cache-size", malo])
    with pytest.raises(SystemExit):
        parse_args(["--cache-size", "mucho"])
