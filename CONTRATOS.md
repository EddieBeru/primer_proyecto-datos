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
