# CONTRATOS C1 ↔ C2 ↔ Vista (Fase 0, Hito 1)

Acuerdos firmados. Cambios solo por regla 6.3 (propuesta escrita + sí del otro + actualizar aquí).

## K1: Proveedor de datos (C1 → C2)

C2 pide, C1 entrega. C2 nunca ve endpoints ni caché:

| Petición | Retorna | Notas |
|---|---|---|
| `listar_criptas()` | `CriptasResponse` (id, nombre, salas, dificultad) | Sin budget (pantalla selección) |
| `preparar_cripta(id)` / `iniciar_cripta(id)` | `(DungeonGeneral, BudgetAdapter)` | Crea el budget con `presupuesto_solicitudes` |
| `sala_lista(n)` | `SalaLista` (room + enemigos/objetos/trampas con ficha) | Nunca ids sueltos; `vida` vacía → `vida_max` |
| `ficha(id)` | `Entidad` del catálogo | Caché primero |
| `budget.get_presupuesto()` | `int` restante | Para C2 y vista modo desarrollo |

Falso (`fake_provider.py`) y real (`room_loader.py`) comparten `SalaLista`: cambiar el import no toca el motor.

## K2: Guardado y carga (provisional, lo cierra C2)

Estado hoy en `savegame.py`: `cripta_id`, `version_cripta`, `version_catalogo`, `sala_actual`, `vida`, `vida_max`, `ataque`, `defensa`, `velocidad`, `presupuesto`, `inventario` (ids en orden). Formato binario propio (`MAGIA + version_fmt + strings con largo + enteros`). Faltan por agregar cuando C2 los entregue: equipo, estado de instancias, puertas, visitadas, agenda, reloj virtual, pila de deshacer. Agregar un campo sin avisar rompe la carga (regla 6.3).

## K3: Bitácora (provisional, formato lo fija C2)

`gamelog.py`: `anotar(linea)` solo agrega al final (vacía → `ValueError`); `leer()` retorna líneas en orden (sin archivo → `[]`, corrupta → `BitacoraError`). Líneas opacas hasta que C2 defina `reloj, tipo, quién, detalle`.

## K4: Errores (`src/models/errors.py`)

| Problema | Clase | Reacción C2 |
|---|---|---|
| 400 petición mal formada | `BadRequestError` | Nuestro bug, no reintentar |
| 404 no existe | `NotFoundError` | Sala inexistente = grave; ficha inexistente = genérico |
| 429 servidor ocupado | `RateLimitedError(reintentar_en)` | Nada: C1 espera y reintenta (máx 3) |
| 500 contenido inválido | `ServerError` | Amable, sin insistir |
| Sin red/timeout | `NetworkError` | Amable + reintentar |
| 200 con forma rara | `UnexpectedResponseError` | Amable, no insistir |
| Presupuesto agotado | `PresupuestoAgotadoError` | Decisión equipo pendiente (doc anterior, Parte 4) |
| Bitácora ilegible | `BitacoraError` | Avisar, no insistir |
| Guardado dañado | `GuardadoError` | Amable, no crash |

## K5: Fachada hacia la Vista (la construye C2)

Intenciones: mover N/S/E/O, atacar, equipar, soltar, recorrer, deshacer, pausar, guardar, cargar, salir, elegir cripta. Foto del estado: sala (nombre, número, puertas y estado), objetos/trampas, jugador (vida, stats, efectos), enemigos (tipo, comportamiento, vida), inventario en orden + equipado, pergaminos, últimos mensajes, solicitudes restantes, estado (jugando/ganó/perdió/pausa), aviso de error. La vista nunca llama a C1 ni al API.

## Enmienda doc oficial (2026-10-15, regla 6.3)

- K1: toda solicitud HTTP cuenta (§5.1), incl lista y reintentos 429. Local/offline no cuenta. Reporte: realizadas/presupuesto/hits/misses.
- K2: EstadoPartida suma semilla, azar_llamadas/azar_estado, acciones_jugador, enemigos_derrotados, puerta_salida_abierta. SalaViva.rastro:int -> ultima_visita:int|None (§2.9). Guardado v2 con índice por sala + core JSON; v1 solo compat.
- K3: bitácora header `#cripta <id> <ver_cripta> <ver_cat> <semilla>` primera línea; replay valida y rehúsa silencioso (§4.11). Pantalla: últimos 20, buffer circular.
- K4: sin cambios de tipos; 429 espera real sin avanzar reloj virtual.
- K5: intenciones suman abrir/esperar/usar. Victoria = entrar salida tras abrir puerta (§2.12). Sin fórmula puntaje: tabla local (nombre, id+versión, acciones, derrotados, reloj).
- Motor: daño `max(1, atk+randint(0,4)-def)` con Random(semilla); intervalo `max(1,costo*100//vel)` con tabla costos; reescale velocidad con seq nuevo; activación orden instancia; errante azar; rastreador vecinas abiertas <400 empate menor id; veneno 80x5; rearme 300 default; regen 200 capada; abrir(50)≠mover(100); trampas auto al entrar; fallos lleno/sin-llave sin tiempo; pergamino por intervalo con exclusión y tope 5.
- Caché: default 25, pin en-uso no desalojable, disco persiste, valida versiones.
- Sorts: mergesort + insertsort, `orden_auto` (n<=32 o casi-ordenado -> inserción).

## Enmienda Sesión/orquestador (2026-10-15, regla 6.3)

- Nueva capa `src/game/` (Sesion + consola): coordina ciclo de vida sin decidir
  reglas ni tocar HTTP/disco directo. C2 nunca ve la Sesión; C1 nunca ve C2.
- K1: la Sesión inyecta `backend` (endpoints/offline/falso) a RoomLoader y
  convierte SalaLista→SalaViva en `ProveedorSesion` (el catálogo vive ahí).
- K2: `Sesion.guardar/cargar` envuelven `fachada.guardar/cargar` + savegame v2;
  `cargar` valida versiones contra el backend de la sesión (mismatch = error,
  nunca silencioso) y recarga fichas referenciadas. Presupuesto restante se
  sincroniza a `estado.presupuesto_restante` tras cada paso (la foto lo expone).
- K3: la Sesión escribe el header `#cripta` al iniciar y vuelca líneas nuevas
  tras cada paso. Replay: valida header vs backend, re-ejecuta vía `paso()`
  (con drenaje §2.3) para fidelidad; líneas de consecuencia se derivan solas.
- K5: loop oficial = intención → drenar agenda hasta turno-jugador/fin → foto.
  Tope 500 eventos por paso; errores de evento = error amable sin crash.
- `savegame.validar_versiones` acepta `backend` (antes cableaba endpoints real).
