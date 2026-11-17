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

- Nueva capa `src/orchestrator/` (Sesion + consola): coordina ciclo de vida sin decidir
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

## Enmienda 002 — 2026-11-08

Autorización explícita del usuario en esta sesión: «apruebo todos los contratos»,
tras presentar la propuesta `specs/002-niebla-ir-a/contracts/interfaces.md`.
Se registra esa aprobación directa, sin atribuir un mensaje a otra persona.

- K1 incorpora `datos_sala(id)->DatosSala` inmutable, desde índice de metadatos
  preparado una vez. Sin HTTP/contenido/fichas/visitas/activaciones. Extremos
  recíprocos opuestos declarados comparten la menor clave; no se inventan inversas.
  La coherencia física y los costos de puertas recíprocas siguen coordinados con001.
- K5 mantiene `(ok,mensaje,FotoEstado)` y suma `ir a <id>`, `cancelar`,
  `avanzar_viaje` y `mapa_conocido`. C2 decide ruta/detención sobre conocimiento;
  un avance ejecuta como máximo un movimiento ordinario y su drenaje. Controles
  y consultas no consumen tiempo. Foto suma viaje y revisión, sin mapa completo.
  Consultas conservan viaje; acciones manuales/guardar/pausa cancelan. Cargar
  solo cancela al instalar correctamente; un fallo preserva la partida/viaje.
- K2 P2 escribe formato3 con conocimiento y deltas reversibles, índice por sala
  y core JSON; rechaza formatos1/2 al cargar una partida P2, sin migración
  silenciosa. Los lectores técnicos legados pueden conservarse por separado.
  No serializa continuación, ruta, contexto de paso, heap ni caché visual.
- K3 añade comentario estricto `#ir-a <id>` una vez por orden aceptada; ambos
  replay lo ignoran, reproduciendo movimientos individuales. Header/corrupción
  conservan sus validaciones. Logs previos sin comentarios siguen siendo legibles;
  lectores antiguos no soportan el comentario nuevo y requieren actualizarse.
- 004 recibe por inyección lotes bidireccionales ordenados y truncamiento de undo
  antes de descartar intervalos por tope cinco. No se implementan historia ni
  checkpoints en002. Su aceptación integrada y la temporal ponderada de001 quedan
  pendientes de entregas reales, igual que el contraste del enunciado íntegro P2.

## Enmienda004 — 2026-11-10

Aprobación explícita del usuario: «apruebo», tras presentar los contratos del
receptor histórico y guardado v4 en specs/004-linea-de-tiempo/contracts/interfaces.md.
El receptor004 es independiente del colector002. Registra deltas completos con
orden causal, cierra acciones después del drenaje y recorta solo el sufijo
revertido; conserva las exclusiones y tope cinco del undo P1. Consultas por
tiempo/ordinal no mutan el motor. Guardado v4 conserva índice <qqq> de v3 y
añade bloque historia versionado al core; el flujo004 rechaza v1/v2/v3 de
forma explícita y valida candidato antes de reemplazar la sesión activa.
Interfaz gráfica con panel navegable, mapa histórico y retícula base8 px según
FR-LIN-15/16. Detalles y garantías en el contrato004 aprobado.

## Enmienda003 — 2026-11-16

Aprobación explícita del usuario en esta sesión: «apruebo todo con tal que se
mantenga consistente con el resto del proyecto. incluyendo decisiones del
diseño», tras revisar las propuestas de
`specs/003-resolubilidad/contracts/interfaces.md` y
`specs/003-resolubilidad/contracts/esqueleto-compartido.md`. Se registra esta
aprobación del usuario sin atribuirla a responsables de001/C1/C2. La integración
queda sujeta a conservar K1/K5, la misma instancia neutral compartida con001,
compatibilidad con002/004, y reglas de interfaz y decisiones ya asentadas.

- K1: el esqueleto compartido añade costo validado (default100), llave opcional
  y estado inicial de puerta; preserva orden fuente e identidad de puertas
  paralelas. Reciprocidad opuesta declarada debe coincidir en costo/llave/estado;
  se rechazan contradicciones y no se inventan inversas. `preparar_metadatos`
  sigue siendo la fuente neutral consumida por001/002/003.
- K1: se agrega `/criptas/{id}/llaves` con validación estricta, versión,
  completitud y orden; cuenta cada intento en el budget. Cache y paquete offline
  validan id/versión y se publican atómicamente. Verificación no descarga
  catálogo/contenido.
- K5: preparación de inicio no crea estado ni vista; el resultado tipado se
  conserva para reporte. Inicio no resoluble se bloquea salvo `--forzar`, y
  datos incompletos nunca se fuerzan. `--verificar` no inicia ni crea vista;
  carga/replay conservan su comportamiento. Consola y vista consumen el mismo
  texto de reporte y la vista recibe Sesión/DTO, sin acceso a C1 ni reglas.
- No se cambian guardado v4 ni las decisiones de `specs/003-resolubilidad/spec.md`.
  Las reglas de presentación siguen `docs/diseno-ui.md`; quedan sujetos a
  verificación los detalles de integración en el código existente y la
  disponibilidad del endpoint/paquete oficial externo.

## 2026-11-16 — Integración001/003 con002/004 (autorización del usuario)

Propuesta aplicada bajo la instrucción «apruebo todas tus recomendaciones» y autorización de conectar las capacidades; no se atribuye aceptación individual a otro compañero. K1 conserva datos_sala neutral, sin llamadas de contenido durante planificación/turno de cazador. K2 añade SalaViva.contenido_pendiente (bool, defaultFalse para datos anteriores): un cazador puede ocupar el esqueleto sin revelar/visitar ni cargar contenido. Al cargarlo se conservan puertas y visitantes y se agregan los habitantes originales. K5 registra esas mutaciones por el receptor existente.

Compatibilidad: guardados con el marcador (en estado o historia) usan cabecera5, mismo índice/JSON que4. Los lectores nuevos admiten4/5 con historia; los antiguos rechazan5 como formato desconocido. Sin marcador se conserva4; no se renumeran bitácoras ni se aceptan silenciosamente guardados1/2/3 como historia completa. El marcadorFalse se omite en serialización y se reconstruye por default. Se mantiene lectura técnica sin historia de formatos anteriores.

2026-11-16, K1/K5: ProveedorSesion expone entradas_sala como índice inverso del mismo esqueleto, construido una sola vez sin contenido; permite campos de distancia compartidos respetando arcos dirigidos. Las búsquedas de rango≤200 siguen siendo individuales locales. K2 mantiene agenda/pila como proyecciones serializadas de las estructuras del motor; _sync es su único escritor en producción y publica deltas de segmento del formato histórico existente. Sin cambio de versión adicional.

2026-11-16, K2/K5: las nuevas inversas de acción incluyen azar_estado_antes/azar_llamadas_antes, sin copiar el estado de partida. Lectura4/5 conservada: si faltan, el retroceso de Sesión obtiene solo esos campos desde deltas de la historia completa004. Se verifica esquema anterior, carga en frío y replay; índices de actores/rutas son transitorios y se reconstruyen al reemplazar EstadoPartida.
