# CRIPTA — Proyecto Estructuras de Datos II-2026

Motor de mazmorra dirigido por eventos. Reglas según doc oficial del profe.

## Requisitos

- Python 3.11+
- `pip install -r requirements.txt`

## Comandos principales

```bash
python -m src.main --help
python -m src.main                       # rutina demo (lista + ficha + sala inicial)
python scripts/exportar_paquete.py       # genera paquete_demo/ offline (sin red)
python -m src.main --offline paquete_demo/    # mismo contrato desde disco, sin gastar red
python -m src.main --semilla 7 --jugador ana
python -m src.main --bench               # mediciones por subsistema (sin red ni vista)
python -m src.main --jugar                # partida interactiva vía Sesión (consola)
python -m src.main --jugar --offline paquete_demo/  # consola sin red ni presupuesto
python -m src.main --vista                # partida gráfica Pygame vía Sesión
python -m src.main --vista --offline paquete_demo/  # vista sin red ni presupuesto
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
| `--vista` | — | partida gráfica Pygame vía Sesión (solo habla con Sesión) |

## Archivos generados

- `partida.bin`: guardado binario v2 (índice por sala, §4.10). v1 solo compat lectura.
- `partida.log`: bitácora append, primera línea `#cripta <id> <ver> <vercat> <semilla>`.
- `puntajes.jsonl`: tabla local (nombre, cripta id+versión, acciones, derrotados, reloj).
- `cache.pkl`: caché LRU persistida (pickle versión + orden).
- `cache.pkl.fichas`: almacén persistente de fichas desalojadas (§4.4, solo si hay `--cache`/ruta real).

## Consola mínima (solo fachada)

`abrir N/S/E/O`, `N/S/E/O` mover, `atacar <inst>`, `esperar`, `pisar <inst>`,
`recoger/usar/equipar/soltar`, `inventario [nombre|peso|valor]` (vista
ordenada sin tocar el orden real, §4.5), `deshacer` (1 pergamino, intervalo
completo), `avanzar` (siguiente evento), `foto`.

## Mapa de carpetas (separación vista–controlador)

| Capa | Carpeta canónica | Contenido |
|---|---|---|
| Controller 1: datos, red y persistencia | `src/controller1/` | `fake_provider`, `client`, `endpoints`, `session`, `offline`, `budget`, `room_loader`, `lru_cache`, `almacen_fichas` (almacén en disco §4.4), `lista_doble`, `tabla_hash`, `mergesort`, `orden`, `savegame`, `gamelog`, `puntajes`, `cli` |
| Controller 2: motor del juego | `src/controller2/` | `modelo`, `agenda` (doble + índices de cancelación), `reloj`, `azar`, `movimiento`, `inventario`, `combate`, `efectos`, `enemigos`, `deshacer`, `victoria`, `bitacora` (formato K3), `buffer_circular` (§4.8), `orden_local` (inserción propia sin C1), `fachada` (K5) |
| Orchestrator (tercer controlador) | `src/orchestrator/` + `src/main.py` | `sesion` (ciclo de vida + drenaje §2.3), `consola` (puente §7.2, solo habla con Sesión), `bench` (mide C1+C2), `main` (entry point) |
| Compartido (contratos, sin dueño) | `src/models/` | formas del API (`dungeons`, `rooms`, `roomContents`, `catalog`, `objects`, `types`) + `errors` (K4) |
| Vista | `src/view/` | Pygame: solo lee `FotoEstado` y envía intenciones a la Sesión (§7.3); `app`, `pantallas`, `capas`, `ui`, `entrada`, `movimiento`, `sprites`, `sfx`, `texto` |

Rutas únicas: solo existen `controller1` / `controller2` / `orchestrator` (más `models`, `view` y `main`).

Reglas: C2 nunca importa `controller1` (sorts llegan inyectados como `orden_fn` vía Sesión); C1 nunca importa `controller2` (bitácora trata líneas como opacas); solo el orquestador ve ambos.

## Mejoras 2026-10 (checklist: `docs/checklist mejoras.md`)

- **Enemigos por todo el mapa.** Al armar una sala se precargan sus vecinas
  del plano como salas *dormidas* (§2.4): errantes/rastreadores pueden
  cruzarlas sin inflar `salas_visitadas` (§2.12). Al activar dormidos se usa
  la velocidad real de la ficha (antes 5 fija). El guardián sigue estático
  por diseño.
- **Trampas: daño, veneno o quemadura.** La ficha puede traer `veneno` y
  `quemadura`/`fuego`; la vista dispara `pisar <instancia>` al pasar por
  encima de una trampa armada (además del disparo al entrar, §2.10).
  Deshacer restaura vida/efectos y cancela pulsos.
- **Salas oscuras.** Campo opcional `oscura`/`oscuridad` (esqueleto o
  contenido) que viaja en el guardado; la vista dibuja velo con halo y lo
  levanta mientras dure el efecto `antorcha`. La consola avisa cómo iluminar.
  Todo probado offline con `paquete_demo/` (sala 3 «Capilla oscura»).
