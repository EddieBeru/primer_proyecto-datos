"""C1-10 Banderas de línea de comandos (§5.3/§4.11/§3.4).

--cache-size N : tope de la CacheLRU (default 25 §4.4, N >= 1).
--replay RUTA  : reproduce la bitácora en vez de jugar (modo C2-11).
--bench        : corre mediciones para el Documento de Decisiones.
--offline DIR  : lee paquete disco vía mismo contrato (no cuenta red).
--semilla N    : semilla RNG de la partida (azar reproducible §2.6).
--jugador NOM  : nombre para la tabla local de puntajes (§2.12).
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
    cache_size: int = 25
    replay: str | None = None
    bench: bool = False
    offline: str | None = None
    semilla: int = 0
    jugador: str = "jugador"
    guardar: str | None = None
    cargar: str | None = None


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="cripta",
        description="Proyecto CRIPTA: explora la cripta, encuentra la llave y sal.",
    )
    parser.add_argument("--cache-size", type=_tamano, default=25,
                        help="tope de fichas en la caché LRU (por defecto 25)")
    parser.add_argument("--replay", default=None,
                        help="ruta de la bitácora a reproducir en vez de jugar")
    parser.add_argument("--bench", action="store_true",
                        help="corre mediciones de rendimiento y sale")
    parser.add_argument("--offline", default=None,
                        help="directorio del paquete offline (no cuenta red)")
    parser.add_argument("--semilla", type=int, default=0,
                        help="semilla RNG de la partida (default 0)")
    parser.add_argument("--jugador", default="jugador",
                        help="nombre para la tabla de puntajes")
    parser.add_argument("--guardar", default=None, help="ruta binaria de guardado")
    parser.add_argument("--cargar", default=None, help="ruta binaria a cargar")
    args = parser.parse_args(argv)
    return CLIConfig(cache_size=args.cache_size, replay=args.replay, bench=args.bench,
                     offline=args.offline, semilla=args.semilla, jugador=args.jugador,
                     guardar=args.guardar, cargar=args.cargar)
