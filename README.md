# CRIPTA — Proyecto Estructuras de Datos II-2026

Motor de mazmorra dirigido por eventos. Reglas según doc oficial del profe.

## Versión

Versión actual: **`@v1.0.0`**. Esta versión está identificada por la etiqueta Git
`@v1.0.0`.

## Parte 2: Codex y GitHub Spec Kit

Para la parte 2 del proyecto se usará **Codex** junto con **GitHub Spec Kit**
para definir las especificaciones, planificar el trabajo, generar tareas e
implementar los cambios.

La configuración, las plantillas y los scripts de Spec Kit se versionan en
`.specify/`; las habilidades de su integración con Codex se versionan en
`.agents/skills/speckit-*/`.

Las especificaciones de las cuatro capacidades están en `specs/`, con su
[índice y flujo de trabajo](docs/capacidades-parte-2.md). Cada capacidad tiene
un `spec.md` y una revisión de calidad; `plan.md` y `tasks.md` se generarán
después de revisar y confirmar su especificación.

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

- `partida.bin`: guardado binario v3 con conocimiento e índice por sala; v1/v2 se leen técnicamente, pero P2 rechaza cargarlos porque no guardan el conocimiento.
- `partida.log`: bitácora append, primera línea `#cripta <id> <ver> <vercat> <semilla>`.
- `puntajes.jsonl`: tabla local (nombre, cripta id+versión, acciones, derrotados, reloj).
- `cache.pkl`: caché LRU persistida (pickle versión + orden).
- `cache.pkl.fichas`: almacén persistente de fichas desalojadas (§4.4, solo si hay `--cache`/ruta real).

## Consola interactiva (solo fachada)

`abrir N/S/E/O`, `N/S/E/O` mover, `atacar <inst>`, `esperar`, `pisar <inst>`,
`recoger/usar/equipar/soltar`, `inventario [nombre|peso|valor]` (vista
ordenada sin tocar el orden real, §4.5), `mapa`, `ir a <id explorado>` y
`cancelar`. Durante un viaje, la consola da un paso cada 150 ms y sigue
aceptando consultas y cancelación. `deshacer` usa 1 pergamino e invierte el
intervalo completo; `guardar`/`cargar` conservan la persistencia; `foto`
consulta el estado actual. El cruce manual por puertas sigue disponible.

En Pygame, **M** abre el mapa gráfico de nodos cuadrados y conexiones
direccionales; **↑/↓/←/→** selecciona la sala vecina en esa dirección y **Enter**
inicia el viaje. **Escape** lo cancela; WASD/flechas regresan al control manual.

## Ventana y controles de Pygame

- **F10** abre Ajustes desde el menú, la pausa o la partida: ventana clásica
  de 1024 × 800, panorámica de 1280 × 720, 1600 × 900 o 1920 × 1080,
  y ayudas de controles. Los tamaños se ajustan al escritorio disponible.
- Arrastra un borde para cambiar el tamaño libremente. **F11** alterna
  pantalla completa y restaura el tamaño anterior de ventana; el arte
  conserva sus proporciones. En panorámica, la mochila y las acciones
  pasan a un panel lateral.
- El juego dibuja directamente a la resolución de la ventana o del
  escritorio en pantalla completa: no usa un frame de resolución fija,
  reescalado de pantalla ni filtros de interpolación. Los sprites se
  ajustan individualmente desde los PNG originales con nearest.
- Textos, botones, mochila, mapa y sprites comparten una escala adaptable:
  crecen en pantallas grandes y se reducen en ventanas pequeñas, conservando
  las proporciones y los alcances de interacción sin ampliar el frame.
- **F2** muestra la guía completa. Los menús aceptan flechas / Tab y Enter,
  los atajos indicados o clic. La mochila acepta clic y rueda del ratón;
  sus botones usan las mismas acciones que el teclado.
- Ajustes y controles suspenden el movimiento y el viaje automático.
  Al perder el foco, el juego se pausa; **Esc** permite continuar.
- Las preferencias se recuerdan al cerrar la ventana, en
  `$XDG_CONFIG_HOME/cripta/ui.json` (por defecto `~/.config/cripta/ui.json`),
  independientemente del guardado de la partida.

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
