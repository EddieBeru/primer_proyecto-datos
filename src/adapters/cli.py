"""C1-10 Banderas de línea de comandos.

--cache-size N : tope de la CacheLRU (N >= 1).
--replay RUTA  : reproduce la bitácora en vez de jugar (modo C2-11).
--bench        : corre mediciones para el informe del Hito 3.
"""

import argparse
from dataclasses import dataclass


def _tamano(valor):
    n = int(valor)
    if n < 1:
        raise argparse.ArgumentTypeError(f"--cache-size debe ser >= 1, llegó {n}")
    return n


@dataclass
class CLIConfig:
    cache_size: int = 50
    replay: str | None = None
    bench: bool = False


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="cripta",
        description="Proyecto CRIPTA: explora la cripta, encuentra la llave y sal.",
    )
    parser.add_argument("--cache-size", type=_tamano, default=50,
                        help="tope de fichas en la caché LRU (por defecto 50)")
    parser.add_argument("--replay", default=None,
                        help="ruta de la bitácora a reproducir en vez de jugar")
    parser.add_argument("--bench", action="store_true",
                        help="corre mediciones de rendimiento y sale")
    args = parser.parse_args(argv)
    return CLIConfig(cache_size=args.cache_size, replay=args.replay, bench=args.bench)
