# Tasks: Verificación de resolubilidad

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [interfaces](contracts/interfaces.md), [esqueleto compartido](contracts/esqueleto-compartido.md) y [quickstart](quickstart.md).

**Prerequisites**: diseño003 completado; propuestas K1/K5 aprobadas por el usuario en esta sesión, con la condición de conservar la arquitectura y decisiones compartidas del proyecto; registro en `CONTRATOS.md`.

**Tests**: solicitados expresamente por el usuario. Escribir y ejecutar primero las pruebas, comprobar que fallan por el comportamiento ausente y después implementar. No marcar una prueba como aprobada por una fixture rota ni sustituirla por un chequeo de importación.

**Organization**: el spec tiene una sola historia, US1 (P1). Setup y fundamentos no tienen etiqueta de historia; todas las tareas de la fase3 tienen `[US1]`. Las fases finales agrupan aceptación transversal y documentación.

## Format: `[ID] [P?] [Story] Description`

Cada tarea usa casilla, ID consecutivo, ruta concreta y referencias FR-RES completas. `[P]` significa trabajo posible en archivos distintos, una vez satisfechas sus dependencias; no autoriza ejecutar tareas dependientes simultáneamente. `Dep:` indica bloqueos explícitos. Todas las referencias a rutas parten de la raíz del repositorio.

## Restricciones que aplican a TODAS las tareas

- Prohibidos `heapq`, `deque`, `set` y `frozenset`, también en pruebas, fixtures, generadores y referencia lenta de003; no sustituirlos mediante alias, imports indirectos ni comprensiones de conjunto. Sus menciones abajo son exclusivamente prohibiciones/auditorías.
- Estructuras propias: cola con arreglo+cursor, pila iterativa, marcas/contadores por ordinal y TablaIndice neutral con hash textual propio. Dict solo transporte JSON/informe, nunca índice o marcas del cálculo; sin `sorted`, `list.sort` ni quitar el frente con `pop(0)`.
- Una exploración incremental de alcanzabilidad. El orden y reporte reutilizan sus evidencias; reducción residual global lineal permitida, sin nuevos recorridos del esqueleto por llave ni expansión de todas las rutas.
- Descubrir una sala no dispara sus salidas: al procesarla, primero llaves según consulta y después N,S,E,O. Pendientes por orden de primera identificación. Para ciclo: primera llave participante según consulta, primer retorno con dependencias según esqueleto/N,S,E,O; reportar alternativas aún bloqueadas.
- Compartir modelo/constructor del esqueleto con001 y conservar integración002/004. Vista consume Sesión/DTO; no accede a C1 ni decide reglas.
- Pruebas de Apéndice B T009–T012 obligatoriamente escritas antes de T019–T033. Las de contratos compartidos T003–T005 anteceden a T006–T008. No ejecutar HTTP real para generar esta lista ni las fixtures.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: fijar contratos y cargas de prueba sin cambiar producción.

- [X] T001 Revisar las propuestas de `specs/003-resolubilidad/contracts/interfaces.md` y `specs/003-resolubilidad/contracts/esqueleto-compartido.md`; registrar la aprobación explícita del usuario y enmienda en `CONTRATOS.md`, condicionadas a mantener la arquitectura K1/K5, la integración001/002/004 y las decisiones de diseño vigentes. (Cubre: FR-RES-01, FR-RES-02, FR-RES-03, FR-RES-08, FR-RES-09, FR-RES-10, FR-RES-11, FR-RES-14, FR-RES-15; Dep: ninguna).
- [X] T002 Preparar constructores de fixtures puras en `tests/fixtures_resolubilidad.py`, preservando orden de páginas/salas/ubicaciones y usando índices propios o secuencias; incluir casos resoluble, ciclo, incompleta, errante con `suelta`, alternativas y costos compartidos; documentar entradas y resultados esperados sin adelantar el algoritmo. (Cubre: FR-RES-01, FR-RES-02, FR-RES-03, FR-RES-05, FR-RES-06, FR-RES-07, FR-RES-12; Dep: T001).

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: modelo neutral y auxiliares comunes. No implementar aún verificación ni política de inicio. Las pruebas de esta fase deben escribirse antes de sus implementaciones; T001 bloquea cambios de contratos.

- [X] T003 Escribir primero pruebas del modelo común en `tests/test_esqueleto.py` y `tests/test_datos_conocimiento.py`: «costo entero≥1(default100)», «cerrada(default falso)», «llave opcional», «no unificar puertas paralelas ni crear inversas», reciprocidad coherente y orden fuente; comprobar falla del comportamiento nuevo antes de T006. (Cubre: FR-RES-01, FR-RES-02, FR-RES-03, FR-RES-05, FR-RES-12, FR-RES-14; Dep: T002).
- [X] T004 [P] Escribir primero pruebas en `tests/test_tabla_indice.py` de claves textuales UTF8, igualdad completa ante colisiones, crecimiento, claves enteras/extremos legados y orden fuente independiente de cubetas; registrar fallo previo a T007. (Cubre: FR-RES-05, FR-RES-07, FR-RES-12; Dep: T002).
- [X] T005 [P] Escribir primero pruebas en `tests/test_cola_fifo.py` de FIFO propia arreglo+cursor, vacía, crecimiento, consumo sin desplazar el frente y memoria O(n); registrar fallo previo a T008. (Cubre: FR-RES-05, FR-RES-12; Dep: T002).
- [X] T006 Ampliar `src/models/rooms.py` y `src/models/conocimiento.py` con costo validado, `llave: str|None`, `cerrada_inicial: bool`, defaults compatibles, colección fuente ordenada e índice neutral; usar una sola instancia/constructor para001/002/003 y rechazar contradicciones recíprocas sin inventar inversas; hacer pasar T003. (Cubre: FR-RES-01, FR-RES-02, FR-RES-03, FR-RES-05, FR-RES-12, FR-RES-14; Dep: T003).
- [X] T007 Ampliar `src/estructuras/tabla_indice.py` con hash propio FNV-1a64 sobre bytes UTF8 y comparación textual completa; conservar claves enteras/extremos y crecimiento amortizado, sin convertir textos a enteros grandes; hacer pasar T004. (Cubre: FR-RES-05, FR-RES-07, FR-RES-12; Dep: T004).
- [X] T008 Implementar FIFO propia encapsulada sobre arreglo y cursor en `src/estructuras/cola_fifo.py`, sin mover elementos al extraer ni retener más de O(n) entradas por verificación; hacer pasar T005. (Cubre: FR-RES-05, FR-RES-12; Dep: T005).

**Checkpoint**: T001–T008 completadas; fundamentos disponibles. Los cambios en pruebas comunes se revisan con001/002.

## Phase 3: User Story 1 - Verificación de resolubilidad (Priority: P1)

**Goal**: comprobar la posibilidad de victoria antes de jugar y presentar orden determinista o causas completas, con modos de inicio, solo verificación y vista.

**Independent Test**: con fixtures offline, verificar los cuatro casos del Apéndice B, comparar orden/reporte en dos ejecuciones, impedir inicio imposible sin forzar, permitirlo forzado y ejecutar solo verificación sin vista. No depender del servidor ni de las funcionalidades del cazador de001.

### Tests for User Story 1 — antes de implementación

Ejecutar T009–T018 y registrar sus fallos esperados antes de T019. T009/T010/T011 comparten archivo y se realizan secuencialmente; las tareas `[P]` usan archivos distintos.

- [X] T009 [US1] Escribir PRUEBA APÉNDICE B1 en `tests/test_resolubilidad.py`: `llave_salida` detrás de la única puerta que ella misma abre produce no resoluble, llave no obtenible, frontera exacta y ciclo concreto con puerta/ubicación; comprobar fallo antes de implementar T022–T026. (Cubre: FR-RES-02, FR-RES-03, FR-RES-06, FR-RES-07, FR-RES-12; Dep: T006, T007, T008).
- [X] T010 [US1] Escribir PRUEBA APÉNDICE B2 en `tests/test_resolubilidad.py`: llave declarada en `suelta` de enemigo errante se obtiene en su sala inicial, incluso si una posición posterior sería diferente; no descargar ficha/contenido para verificar; comprobar fallo antes de T019–T023. (Cubre: FR-RES-01, FR-RES-02, FR-RES-11; Dep: T009).
- [X] T011 [US1] Escribir PRUEBA APÉNDICE B3 en `tests/test_resolubilidad.py`: varios órdenes válidos dan el mismo orden en dos ejecuciones y100 repeticiones; caso Z por N antes de A por E, llaves locales según consulta, puertas pendientes por identificación y llave obtenida antes de alcanzar su puerta; comprobar fallo antes de T023/T024. (Cubre: FR-RES-04, FR-RES-05, FR-RES-12; Dep: T010).
- [X] T012 [P] [US1] Escribir PRUEBA APÉNDICE B4 en `tests/test_sesion_resolubilidad.py`: cripta no resoluble sin `--forzar` no crea estado, enemigos ni bitácora y expone reporte; forzada inicia con el mismo negativo, incompleta jamás se fuerza y fallo preserva una sesión previa; usar resultado negativo inyectado para aislar la política; comprobar fallo antes de T029/T030. (Cubre: FR-RES-01, FR-RES-08, FR-RES-10, FR-RES-14, FR-RES-15; Dep: T006, T007, T008).
- [X] T013 [US1] Completar pruebas del núcleo en `tests/test_resolubilidad.py`: salida final por puerta requerida frente a entrada alternativa, llave opcional inaccesible, no consumo, trampas/cierres ignorados, frontera final, ciclos múltiples deterministas, A por B O C con B/C tras A, alternativa luego accesible, circuito de salas sin llave, regiones desconectadas, llaves ausentes y error por puerta sin llave; agregar contadores y comprobar fallo previo a T022–T026. (Cubre: FR-RES-02, FR-RES-03, FR-RES-04, FR-RES-05, FR-RES-06, FR-RES-07, FR-RES-12, FR-RES-14, FR-RES-15; Dep: T011).
- [X] T014 [P] [US1] Escribir pruebas de contrato en `tests/test_llaves.py` para `GET /criptas/{id}/llaves`, parsing/orden, enemigo en inicio, tipos estrictos, respuesta completa,404/429/red/versión distinta, conteo de cada intento y presupuesto agotado sin petición; simular transporte y comprobar fallo previo a T019/T020. (Cubre: FR-RES-01, FR-RES-02, FR-RES-11, FR-RES-14; Dep: T006, T007, T008).
- [X] T015 [P] [US1] Escribir pruebas en `tests/test_almacen_llaves.py` de id/versión/formato1, escritura atómica, caché vigente/obsoleta/corrupta, orden persistido, offline cero HTTP y paquete antiguo sin archivo; comprobar fallo previo a T021. (Cubre: FR-RES-11, FR-RES-14; Dep: T006, T007, T008).
- [X] T016 [P] [US1] Escribir pruebas CLI en `tests/test_cli_resolubilidad.py`: forzar/verificar, códigos0/1/2, verificar con forzar/vista/jugar sin crear partida ni importar/instanciar vista, incompatibilidad con replay/cargar/bench, ids contradictorios y ningún catálogo/contenido ni lista ficticia; comprobar fallo previo a T028–T032. (Cubre: FR-RES-08, FR-RES-09, FR-RES-11, FR-RES-14, FR-RES-15; Dep: T006, T007, T008).
- [X] T017 [P] [US1] Escribir pruebas de contrato gráfico en `tests/test_vista_resolubilidad.py`: resultado visible aun sin FotoEstado nueva, igualdad textual con CLI, continuar/volver, error no forzable, foco/scroll/IDs largos y acceso completo; usar DTO falso y SDL dummy, sin reglas de motor ni acceso C1 desde vista; comprobar fallo previo a T027/T033. (Cubre: FR-RES-08, FR-RES-10, FR-RES-14, FR-RES-15; Dep: T006, T007, T008).
- [X] T018 [P] [US1] Escribir pruebas en `tests/test_bench_resolubilidad.py`: sintéticas por semilla, igualdad de entradas entre métodos, veredicto/llaves/validez de orden, visitas acotadas, fases temporizadas y registro003 en bench; comprobar fallo previo a T035–T037. (Cubre: FR-RES-03, FR-RES-04, FR-RES-05, FR-RES-06, FR-RES-07, FR-RES-12, FR-RES-13; Dep: T006, T007, T008).

### Implementation for User Story 1

**Gate de pruebas**: T009–T018 escritas y ejecutadas antes de T019. Las tareas siguientes hacen pasar esas pruebas; no reescribir sus expectativas para acomodar el código.

- [X] T019 [US1] Definir DTO inmutables en `src/models/resolubilidad.py`: UbicacionesLlaves, UbicacionLlave y ResultadoResolubilidad; validar «identidad por id de llave, ordinal por primera aparición», «Varias ubicaciones del mismo id son alternativas», «Sala desconocida o versión distinta es error», enemigo opcional siempre referido a sala inicial y «Colecciones inmutables, IDs completos»; distinguir completa/incompleta de llave ausente y respetar «preparando → incompleta | propagando → resumiendo → resoluble | no_resoluble». (Cubre: FR-RES-02, FR-RES-03, FR-RES-04, FR-RES-06, FR-RES-07, FR-RES-11, FR-RES-14, FR-RES-15; Dep: T009, T010, T011, T012, T013, T014, T015, T016, T017, T018).
- [X] T020 [US1] Consumir `/criptas/{id}/llaves` en `src/controller1/endpoints.py` con el DTO de T019 y el mismo budget, validación estricta y reintentos contados; propagar404/consulta incompleta como error, sin descargar catálogo/contenido ni inferir ubicaciones; hacer pasar T014. (Cubre: FR-RES-01, FR-RES-02, FR-RES-11, FR-RES-14; Dep: T019).
- [X] T021 [US1] Implementar persistencia por id/versión/formato1 en `src/controller1/almacen_llaves.py` y lectura `llaves_<id>.json` en `src/controller1/offline.py`; validar integridad/completitud/orden antes de publicar atómicamente, invalidar mismatch y no consumir red al leer local; conservar guardado v4; hacer pasar T015. (Cubre: FR-RES-11, FR-RES-14; Dep: T019, T020).
- [X] T022 [US1] Compilar en `src/algoritmos/resolubilidad.py` una vez el modelo común y ubicaciones a reglas sala→sala, sala Y llave→sala y sala→llave, con incidencias inversas, ordinales compactos y evidencia compartida; «nunca arreglos dimensionados por max(id)»; conservar todas las alternativas, validar incluso puertas de salas inalcanzables y no producir todas las parejas de llaves de un camino. (Cubre: FR-RES-01, FR-RES-02, FR-RES-03, FR-RES-06, FR-RES-07, FR-RES-12, FR-RES-14; Dep: T019, T006, T007, T008).
- [X] T023 [US1] Implementar en `src/algoritmos/resolubilidad.py` la propagación monotónica con FIFO propia, contadores/suscriptores y pendientes por llave: marcar/encolar al descubrir, recoger llaves antes de habilitar salidas N,S,E,O al procesar, sin reactivar salidas al descubrir ni repetir recorrido por llave; conservar testigos de primera entrada y no tocar reloj/RNG/estado vivo; hacer pasar B2. (Cubre: FR-RES-01, FR-RES-02, FR-RES-03, FR-RES-04, FR-RES-05, FR-RES-12; Dep: T022).
- [X] T024 [US1] Completar en `src/algoritmos/resolubilidad.py` el orden realizable de cada llave obtenible una sola vez, pendientes por primera identificación y cierre hasta agotar avance aun después de victoria; exigir llave final y acceso hacia sala final por puerta que la requiere, sin exigir llaves opcionales inaccesibles; hacer pasar B3 y los contadores de T013. (Cubre: FR-RES-03, FR-RES-04, FR-RES-05, FR-RES-12; Dep: T023).
- [X] T025 [US1] Construir en `src/algoritmos/resolubilidad.py` el resumen de llaves no obtenibles, ubicaciones, condiciones de victoria incumplidas y frontera FINAL mediante marcas/evidencia del mismo recorrido; excluir puertas internas y habilitadas, conservar categorías vacías y ubicación no declarada, sin nuevas búsquedas por llave. (Cubre: FR-RES-03, FR-RES-06, FR-RES-12, FR-RES-14, FR-RES-15; Dep: T024).
- [X] T026 [US1] Implementar en `src/algoritmos/resolubilidad.py` Tarjan iterativo propio sobre evidencia residual compartida, selección lineal de primera llave participante por orden de consulta y una sola búsqueda de primer retorno con orden fuente/N,S,E,O; reportar circuito con puertas/ubicaciones y otras alternativas bloqueadas, ignorando ciclos de salas sin llave, sin enumerar todas las rutas/ciclos ni recorrer esqueleto por llave; hacer pasar B1 y T013. (Cubre: FR-RES-06, FR-RES-07, FR-RES-12, FR-RES-15; Dep: T025).
- [X] T027 [US1] Implementar `texto_reporte` en `src/orchestrator/reporte_resolubilidad.py` con encabezados/orden/literales FR-RES-15, ubicaciones completas, motivo de incompleta y alternativas del ciclo; una sola emisión por evidencia con referencias estables para evitar expansión del texto; consola y vista consumen exactamente ese contenido. (Cubre: FR-RES-04, FR-RES-06, FR-RES-07, FR-RES-09, FR-RES-10, FR-RES-14, FR-RES-15; Dep: T026).
- [X] T028 [US1] Corregir bootstrap presupuestado en `src/controller1/session.py` y sus pruebas de `tests/test_budget.py`: contar datos generales, intentos y solo listas realmente realizadas, no descontar lista ficticia en id directo ni silenciar agotamiento; mantener un único BudgetAdapter entre preparación e inicio. (Cubre: FR-RES-01, FR-RES-09, FR-RES-11, FR-RES-14; Dep: T020, T021, T016).
- [X] T029 [US1] Añadir preparación de inicio en `src/orchestrator/sesion.py` que obtiene info/modelo compartido/llaves, verifica una sola vez y conserva resultado/budget/plano sin crear catálogo, estado, enemigos, bitácora o vista; reutilizar preparación válida al confirmar e invalidarla al cambiar id/versión, distinguiendo incompleta de imposible. (Cubre: FR-RES-01, FR-RES-08, FR-RES-09, FR-RES-10, FR-RES-11, FR-RES-14; Dep: T027, T028).
- [X] T030 [US1] Integrar `iniciar(..., forzar=False)` y `reporte_inicio()` en `src/orchestrator/sesion.py`: bloquear negativo sin forzar y cualquier incompleta, devolver FotoEstado en éxito y DTO en fallo tipado, instalar estado solo tras confirmar y preservar estado previo ante error; separar inicialización técnica de carga/replay para no verificar ni bloquear partidas antiguas/forzadas; hacer pasar B4. (Cubre: FR-RES-01, FR-RES-08, FR-RES-10, FR-RES-11, FR-RES-14, FR-RES-15; Dep: T029, T012).
- [X] T031 [US1] Agregar configuración/parser de `--forzar` y `--verificar <cripta>` en `src/controller1/cli.py` con las combinaciones definidas en contratos: verificar prevalece sobre vista/jugar y forzar no inicia; rechazar replay/cargar/bench e ids contradictorios antes de HTTP/vista. (Cubre: FR-RES-08, FR-RES-09, FR-RES-14; Dep: T016, T019).
- [X] T032 [US1] Integrar el despacho de verificar en `src/main.py` antes de vista/Pygame y transmitir forzar a todas las rutas de NUEVA partida; imprimir reporte común con códigos0/1/2, sin crear estado/log/catálogo/contenido en solo verificación y sin aplicar la política a cargar/replay; hacer pasar T016. (Cubre: FR-RES-08, FR-RES-09, FR-RES-11, FR-RES-14, FR-RES-15; Dep: T030, T031, T027).
- [X] T033 [US1] Leer `docs/diseno-ui.md` y presentar reporte vía Sesión/DTO en `src/view/app.py` y `src/view/pantallas.py`, incluso inicio bloqueado: continuar/volver, aviso de forzado y scroll/foco/IDs completos; reutilizar tokens/paneles rectos, cuerpo14–16 px, auxiliar≥11 px, interlineado múltiplo4 y contraste4.5:1 normal/3:1 solo grande; no introducir auxiliares prohibidos ni reglas del motor en vista. (Cubre: FR-RES-08, FR-RES-10, FR-RES-14, FR-RES-15; Dep: T017, T030, T032).
- [X] T034 [US1] Completar paquetes offline de integración en `tests/fixtures/resolubilidad/` y falsos de `tests/fixtures_resolubilidad.py` con datos generales, esqueleto y llaves de igual versión; añadir catálogo/contenido solo para jugar, mantener consulta pura sin ellos y actualizar fixtures afectadas en `tests/test_sesion.py` sin bypass silencioso de verificación. (Cubre: FR-RES-01, FR-RES-02, FR-RES-08, FR-RES-09, FR-RES-10, FR-RES-11, FR-RES-14; Dep: T020, T021, T030).
- [X] T035 [US1] Crear familias sintéticas deterministas por semilla300316 en `src/orchestrator/bench_resolubilidad.py`: cadenas128/512/2048/8192 llaves, ciclo, muchos pendientes por llave, alternativas y desconexión; ids dispersos/orden controlado, E≤4S y mismos insumos para ambos métodos, generación fuera del cronómetro. (Cubre: FR-RES-03, FR-RES-04, FR-RES-05, FR-RES-06, FR-RES-07, FR-RES-12, FR-RES-13; Dep: T018, T026).
- [X] T036 [US1] Añadir a `src/orchestrator/bench_resolubilidad.py` referencia lenta de laboratorio que recorre el plano por cada llave nueva, aislada del verificador de producción y sin auxiliares prohibidos; comparar veredicto, obtenibles y validez del orden con incremental, usando fixtures pequeñas para oráculo del ciclo y sin exigir el mismo desempate a la referencia. (Cubre: FR-RES-03, FR-RES-04, FR-RES-05, FR-RES-06, FR-RES-07, FR-RES-12, FR-RES-13; Dep: T035).
- [X] T037 [US1] Integrar sección003 en `src/orchestrator/bench.py` y salida de `src/main.py`: dos calentamientos,≥7 muestras por familia/tamaño, perf_counter_ns, total local y desglose compilación/propagación/resumen/texto, contadores de visitas, mediana/máximo, equipo/CPU/intérprete/commit/semilla/S/E/K/L/bytes/reporte; medir memoria aparte y distinguir subsistemas legados ajenos a003. (Cubre: FR-RES-12, FR-RES-13; Dep: T036, T032).
- [X] T038 [US1] Ejecutar las pruebas B1/B2/B3 de `tests/test_resolubilidad.py`, contratos de `tests/test_llaves.py`/`tests/test_almacen_llaves.py` y contadores lineales; corregir fallos sin debilitar expectativas y registrar resultados/comandos en `specs/003-resolubilidad/quickstart.md`. (Cubre: FR-RES-01, FR-RES-02, FR-RES-03, FR-RES-04, FR-RES-05, FR-RES-06, FR-RES-07, FR-RES-11, FR-RES-12, FR-RES-14, FR-RES-15; Dep: T026, T027, T034).
- [X] T039 [US1] Ejecutar B4 de `tests/test_sesion_resolubilidad.py`, subprocess de `tests/test_cli_resolubilidad.py`, SDL dummy de `tests/test_vista_resolubilidad.py` y pruebas de `tests/test_bench_resolubilidad.py`; comprobar igualdad de reporte, modos sin vista, forzado y errores, y registrar evidencia en `specs/003-resolubilidad/quickstart.md`. (Cubre: FR-RES-08, FR-RES-09, FR-RES-10, FR-RES-11, FR-RES-12, FR-RES-13, FR-RES-14, FR-RES-15; Dep: T033, T034, T037, T038).

**Checkpoint US1**: T009–T039 completadas: una historia completa, probada sin servidor, con reporte/orden, inicio protegido, CLI/UI y benchmark. La aceptación temporal con cripta publicada sigue separada.

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: auditoría, integración001/002/004, evidencia de rendimiento y documentación. No marcar aceptación de200 ms mediante las cifras preliminares de estructuras.

- [X] T040 Añadir/ejecutar auditoría en `tests/test_restricciones_resolubilidad.py` de AST/imports/aliases/comprensiones y dependencias transitivas del flujo puro/preparador para PROHIBIR heapq, deque, set y frozenset; revisar además dict como índice, ordenamientos prohibidos y recorridos por llave; incluir archivos nuevos de pruebas/bench y auxiliares de reporte, documentar legados ajenos sin declarar cumplimiento global. (Cubre: FR-RES-05, FR-RES-07, FR-RES-09, FR-RES-12, FR-RES-13; Dep: T039).
- [X] T041 Ejecutar pruebas compartidas de `tests/test_esqueleto.py`, `tests/test_datos_conocimiento.py`, `tests/test_tabla_indice.py`, `tests/test_viaje.py`, `tests/test_historia.py`, `tests/test_cli_historia.py`, `tests/test_savegame.py` y `tests/test_sesion.py`; comprobar misma instancia del esqueleto001/003, costos/puertas y ausencia de consultas nuevas en cargar/replay; registrar límites externos de001 en `specs/003-resolubilidad/quickstart.md`. (Cubre: FR-RES-01, FR-RES-02, FR-RES-03, FR-RES-05, FR-RES-08, FR-RES-09, FR-RES-11, FR-RES-12, FR-RES-14; Dep: T040).
- [X] T042 Ejecutar `.venv/bin/python -m pytest tests/ -q` y `git diff --check`, corregir regresiones pertinentes y registrar conteos/fallos/omitidas con comando en `specs/003-resolubilidad/quickstart.md`, sin afirmar pruebas no ejecutadas. (Cubre: FR-RES-01, FR-RES-02, FR-RES-03, FR-RES-04, FR-RES-05, FR-RES-06, FR-RES-07, FR-RES-08, FR-RES-09, FR-RES-10, FR-RES-11, FR-RES-12, FR-RES-13, FR-RES-14, FR-RES-15; Dep: T041).
- [X] T043 Ejecutar `--bench` de003 conforme a `specs/003-resolubilidad/quickstart.md` y guardar muestras/contadores por semilla/tamaño/familia en `docs/mediciones/003-resolubilidad-sinteticas.json`; demostrar trabajo acotado por tamaño frente al factor de llaves del comparador, incluir resumen/ciclo/texto y revisar colisiones/longitudes de ids sin presentar sintéticas como cripta oficial. (Cubre: FR-RES-05, FR-RES-07, FR-RES-12, FR-RES-13; Dep: T037, T040, T042).
- [X] T044 Identificar versión/tamaño del paquete de la mayor cripta publicada y ejecutar100 verificaciones completas (preparación local+propagación+resumen+ciclo+texto, sin red/render), guardando todas las muestras y máximo en `docs/mediciones/003-resolubilidad-publicada.json`; aceptar solo si todas≤200 ms. Si no hay paquete verificable, registrar bloqueo externo en `specs/003-resolubilidad/quickstart.md` y dejar ESTA tarea pendiente, sin sustituirla por sintéticas. (Cubre: FR-RES-12; Dep: T043).
- [X] T045 Revisar reporte/menú, HUD, mapa e historial a640×480,1024×800 y1280×720, con nombres/errores largos y navegación por foco/ratón; guardar capturas en `docs/mediciones/003-reporte/` y evidencia de contraste/acceso completo en `specs/003-resolubilidad/quickstart.md`, distinguiendo revisión headless y recorrido humano. (Cubre: FR-RES-08, FR-RES-10, FR-RES-14, FR-RES-15; Dep: T033, T039).
- [X] T046 Actualizar `README.md`, `DECISIONES.md` y `PROMPTS_LLM.md` con banderas/endpoint/offline, estructuras elegidas y alternativas, mediciones reales de T043/T044, complejidad esperada/bytes/colisiones y límites; enlazar comandos reproducibles y reflejar que los200 ms siguen pendientes si T044 no pudo ejecutarse. (Cubre: FR-RES-08, FR-RES-09, FR-RES-10, FR-RES-11, FR-RES-12, FR-RES-13, FR-RES-14, FR-RES-15; Dep: T043, T045).
- [X] T047 Cerrar matriz de los15 requisitos y13 escenarios en `specs/003-resolubilidad/quickstart.md`, vinculando cada prueba/evidencia y revisando `specs/003-resolubilidad/tasks.md`; no marcar tareas bloqueadas/comprobaciones pendientes como hechas, comprobar otra vez prohibiciones y ejecutar `git diff --check` antes de entrega. (Cubre: FR-RES-01, FR-RES-02, FR-RES-03, FR-RES-04, FR-RES-05, FR-RES-06, FR-RES-07, FR-RES-08, FR-RES-09, FR-RES-10, FR-RES-11, FR-RES-12, FR-RES-13, FR-RES-14, FR-RES-15; Dep: T042, T043, T045, T046).

## Dependencies & Execution Order

### Phase Dependencies

1. Setup T001–T002: acuerdo de contratos y fixtures iniciales. T001 no se da por aprobada al generar este documento.
2. Fundamentos T003–T008: pruebas antes de modelo/índice/FIFO. T006 depende de T003; T007 de T004; T008 de T005. US1 exige todos los fundamentos terminados.
3. US1 T009–T039: escribir y ejecutar todas las pruebas T009–T018 antes de T019; luego implementar modelos/cliente, núcleo, reporte e integraciones según `Dep:`. Una casilla de prueba temprana significa prueba escrita y fallo esperado registrado; la aprobación funcional se verifica en T038/T039.
4. Transversales T040–T047: auditoría y regresión antes de medir el producto; documentación declara cualquier bloqueo de aceptación. T047 puede inventariar pendientes de T044, pero no declarar aceptación completa mientras T044 siga pendiente.

### Dependency graph

```text
T001 -> T002 -> {T003,T004,T005}
T003 -> T006; T004 -> T007; T005 -> T008
{T006,T007,T008} -> [pruebas T009..T018] -> T019
T019 -> T020 -> T021
T019 -> T022 -> T023 -> T024 -> T025 -> T026 -> T027
{T020,T021,T016} -> T028
{T027,T028} -> T029 -> T030
{T016,T019} -> T031
{T030,T031,T027} -> T032 -> T033
{T020,T021,T030} -> T034
{T018,T026} -> T035 -> T036
{T036,T032} -> T037
{T026,T027,T034} -> T038
{T033,T034,T037,T038} -> T039 -> T040 -> T041 -> T042
{T037,T040,T042} -> T043 -> T044 [paquete publicado]
{T033,T039} -> T045
{T043,T045} -> T046
{T042,T043,T045,T046} -> T047 [no oculta T044 pendiente]
```

El grafo muestra las ramas principales; las listas `Dep:` de cada tarea son la referencia completa. Un ID menor no implica que pueda saltarse la compuerta de pruebas o la aprobación de contratos.

### Trazabilidad de los cuatro escenarios del Apéndice B

| Escenario | Prueba escrita primero | Implementación posterior | Comprobación de aprobación |
|---|---|---|---|
| B1: llave final tras su propia puerta, negativo y ciclo | T009 | T022–T027 | T038 |
| B2: llave en `suelta` de errante, ubicación inicial | T010 | T019–T024 | T038 |
| B3: varios órdenes, mismo resultado | T011 | T023–T024 | T038 |
| B4: imposible sin forzar, sin partida y con reporte | T012 | T029–T033 | T039 |

### Cobertura por requisito

| Requisito | Implementación principal | Pruebas/aceptación |
|---|---|---|
| FR-RES-01 | T020,T022,T023,T029,T030 | T009,T010,T012,T038 |
| FR-RES-02 | T006,T019,T020,T022,T023 | T003,T010,T013,T014,T038 |
| FR-RES-03 | T022,T023,T024,T025 | T009,T013,T038 |
| FR-RES-04 | T023,T024,T027 | T011,T013,T038 |
| FR-RES-05 | T007,T008,T023,T024 | T004,T005,T011,T040 |
| FR-RES-06 | T025,T026,T027 | T009,T013,T038 |
| FR-RES-07 | T026,T027 | T009,T013,T038,T040 |
| FR-RES-08 | T029,T030,T031,T032,T033 | T012,T016,T017,T039 |
| FR-RES-09 | T029,T031,T032 | T016,T039,T040 |
| FR-RES-10 | T027,T029,T030,T033 | T012,T017,T039,T045 |
| FR-RES-11 | T019,T020,T021,T028,T029 | T010,T014,T015,T016,T038 |
| FR-RES-12 | T007,T008,T022–T026,T035–T037 | T013,T018,T040,T043,T044 |
| FR-RES-13 | T035,T036,T037 | T018,T039,T043 |
| FR-RES-14 | T019,T020,T021,T028,T029,T030 | T012–T017,T038,T039 |
| FR-RES-15 | T019,T025,T026,T027,T033 | T013,T016,T017,T038,T039,T045 |

## Parallel Example: User Story 1

Una vez completados T001–T008, pueden escribirse en paralelo T012 (`tests/test_sesion_resolubilidad.py`), T014 (`tests/test_llaves.py`), T015 (`tests/test_almacen_llaves.py`), T016 (`tests/test_cli_resolubilidad.py`), T017 (`tests/test_vista_resolubilidad.py`) y T018 (`tests/test_bench_resolubilidad.py`), mientras la secuencia T009→T010→T011→T013 se mantiene en `tests/test_resolubilidad.py`. Todos usan fixtures ya preparadas y contratos acordados; no editan a la vez las fixtures compartidas.

En fundamentos, T004 y T005 pueden escribirse en paralelo entre sí y con T003 porque usan archivos distintos. Las implementaciones del núcleo T022–T026 se serializan por compartir `src/algoritmos/resolubilidad.py`. No se marcan como paralelas las integraciones que comparten Sesión, main, bench o quickstart.

Estas oportunidades describen orden de trabajo; no solicitan crear subagentes ni ejecutar implementación durante `$speckit-tasks`.

## Implementation Strategy

### MVP First: User Story 1

US1 es la única historia del spec; el MVP de usuario cubre el núcleo y las integraciones T001–T034; B1–B4 se comprueban en T038/T039 y este último checkpoint requiere también T035–T037. Por tanto, el primer hito aprobable con estas dependencias es T001–T039. No fragmentar artificialmente el spec creando US2/US3 ni llamar MVP terminado a un verificador que omite el diagnóstico. La entrega completa exige además benchmark, auditoría, regresión, documentación y aceptación del rendimiento.

### Incremental Delivery

1. Contratos/fundamentos probados: T001–T008.
2. Pruebas de comportamiento escritas antes del código: T009–T018.
3. DTO/endpoint/persistencia: T019–T021; núcleo y reporte: T022–T027.
4. Preparación e inicio seguro: T028–T030; parser/CLI/UI y fixtures: T031–T034.
5. Instrumentación comparativa y aprobación funcional: T035–T039.
6. Auditoría/regresión/medición/revisión visual/documentación: T040–T047. Un bloqueo externo en la cripta publicada se mantiene explícito en T044 y no se sustituye por datos sintéticos.

## Validación de generación

47 tareas:2 de setup,6 de fundamentos,31 de US1 y8 transversales. Ocho tareas marcadas `[P]`. Todas tienen casilla sin marcar, ID consecutivo, ruta concreta, referencias FR-RES y dependencias previas; no se ha implementado ni ejecutado ninguna de ellas al generar esta lista. Las cuatro pruebas de Apéndice B preceden al código correspondiente. Las únicas menciones de heapq/deque/set son prohibiciones o auditoría; ninguna tarea autoriza introducirlos.

No existe `.specify/extensions.yml`: no hay hooks previos ni posteriores de generación de tareas que ejecutar.
