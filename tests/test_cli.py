"""C1-10: CLI parsea banderas y valida, sin red ni archivos."""

import pytest

from src.controller1.cli import CLIConfig, parse_args


def test_defaults():
    cfg = parse_args([])
    assert cfg == CLIConfig(cache_size=25, replay=None, bench=False)


def test_banderas():
    cfg = parse_args(["--cache-size", "20", "--replay", "juego.log", "--bench",
                      "--offline", "pk", "--semilla", "7", "--jugador", "ana",
                      "--jugar"])
    assert cfg.cache_size == 20
    assert cfg.replay == "juego.log"
    assert cfg.bench is True
    assert cfg.offline == "pk"
    assert cfg.semilla == 7
    assert cfg.jugador == "ana"
    assert cfg.jugar is True


def test_cache_size_invalido():
    for malo in ("0", "-3"):
        with pytest.raises(SystemExit):
            parse_args(["--cache-size", malo])
    with pytest.raises(SystemExit):
        parse_args(["--cache-size", "mucho"])
