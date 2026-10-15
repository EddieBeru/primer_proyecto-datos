# CRIPTA — Proyecto Estructuras de Datos II-2026

Motor de mazmorra dirigido por eventos. Reglas según doc oficial del profe.

## Requisitos

- Python 3.11+
- `pip install -r requirements.txt`

## Comandos principales

```bash
python -m src.main --help
python -m src.main                       # rutina demo (lista + ficha + sala inicial)
python -m src.main --offline paquete/    # mismo contrato desde disco, sin gastar red
python -m src.main --semilla 7 --jugador ana
python -m src.main --bench               # mediciones por subsistema (sin red ni vista)
python -m src.main --jugar                # partida interactiva vía Sesión (consola)
python -m src.main --replay partida.log --cargar partida.bin
python -m pytest tests/ -q
```

## Banderas

| Bandera | Default | Qué hace |
|---|---|---|
| `--cache-size N` | 25 | tope fichas caché LRU (§4.4) |
| `--replay RUTA` | — | reproduce bitácora sin interacción (§4.11) |
| `--bench` | — | cargas sintéticas por subsistema (§5.3) |
| `--offline DIR` | — | paquete disco, no cuenta red (§3.4) |
| `--semilla N` | 0 | RNG reproducible (§2.6) |
| `--jugador NOM` | jugador | tabla local puntajes (§2.12) |
| `--jugar` | — | partida interactiva en consola vía Sesión |

## Archivos generados

- `partida.bin`: guardado binario v2 (índice por sala, §4.10). v1 solo compat lectura.
- `partida.log`: bitácora append, primera línea `#cripta <id> <ver> <vercat> <semilla>`.
- `puntajes.jsonl`: tabla local (nombre, cripta id+versión, acciones, derrotados, reloj).
- `cache.pkl`: caché LRU persistida (pickle versión + orden).

## Consola mínima (solo fachada)

`abrir N/S/E/O`, `N/S/E/O` mover, `atacar <inst>`, `esperar`, `recoger/usar/equipar/soltar`,
`deshacer` (1 pergamino, intervalo completo), `avanzar` (siguiente evento), `foto`.
