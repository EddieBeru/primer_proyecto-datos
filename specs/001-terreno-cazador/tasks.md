# Tasks: Terreno y cazador (001)

**Input**: Documentos de diseño de `/specs/001-terreno-cazador/` (`spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/interfaces.md`, `quickstart.md`).

**Prerequisites**: `plan.md` (aprobado), `spec.md` (aclarado con 5 preguntas ratificadas), `research.md`, `data-model.md`, `contracts/interfaces.md`.

**Tests**: Se adopta un enfoque TDD riguroso. Cada fase de historia de usuario define sus tareas de pruebas automatizadas antes de las tareas de implementación, cubriendo inequívocamente los 7 escenarios de aceptación del Apéndice B y los casos límite.

**Organization**: Tareas agrupadas por fases e historias de usuario (US1 a US4) para permitir implementación y verificación modular e independiente.

**Restricción de Integridad Algorítmica**: Está **PROHIBIDO** el uso de `heapq`, `deque` y `set` (ni como estructura auxiliar). No se admiten en ninguna tarea o archivo de código nuevo. Todas las operaciones de cola con prioridad y tablas indexadas emplean `MonticuloMinimo` y `TablaIndice` propios de `src/estructuras/`.

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Ejecutable en paralelo (archivos independientes, sin dependencias pendientes).
- **[Story]**: Historia de usuario a la que pertenece ([US1], [US2], [US3], [US4]).
- Cada tarea incluye rutas de archivo exactas y trazabilidad a requisitos funcionales `[FR-CAZ-xx]`.

---

## Phase 1: Setup (Infraestructura compartida y validación inicial)

**Purpose**: Verificación de herramientas, estructuras base sin dependencias prohibidas y preparación del arnés de pruebas.

- [X] T001 Verificar entorno de ejecución Python y validar que `src/estructuras/monticulo_minimo.py` y `src/estructuras/tabla_indice.py` no importen ni utilicen `heapq`, `deque` ni `set` [FR-CAZ-14]
- [X] T002 [P] Crear el andamio del archivo de pruebas unitarias y de integración en `tests/test_terreno_cazador.py` con fixtures sintéticos de criptas, salidas con costos y catálogo de enemigos [FR-CAZ-01, FR-CAZ-04]

---

## Phase 2: Foundational (Prerrequisitos bloqueantes)

**Purpose**: Extensiones estructurales a modelos de datos y algoritmos base que bloquean la implementación de las historias de usuario.

⚠️ **CRITICAL**: Ninguna historia de usuario puede implementarse hasta completar esta fase.

- [X] T003 [P] Extender `Exit` en `src/models/rooms.py` agregando el atributo `costo: int = 100` con validación "entero mayor o igual que 1, predeterminado en 100" [FR-CAZ-01]
- [X] T004 [P] Extender `SalidaViva` en `src/controller2/modelo.py` agregando `costo: int = 100` con validación "entero mayor o igual que 1, simétrico en ambos sentidos" e hidratación desde `Exit.costo` [FR-CAZ-01]
- [X] T005 [P] Extender `Enemy` en `src/models/catalog.py` incorporando el comportamiento `"cazador"` y el campo `rango: Optional[int] = None` con validación "entero mayor o igual que 1 obligatorio si comportamiento es cazador" [FR-CAZ-04]
- [X] T006 [P] Extender `EstadoPartida` en `src/controller2/modelo.py` agregando el contador en memoria `puertas_version: int = 0` para invalidación $O(1)$ de rutas [FR-CAZ-11]
- [X] T007 [P] Crear el módulo `src/controller2/rutas.py` con la estructura base de búsqueda de caminos óptimos usando exclusivamente `MonticuloMinimo` y `TablaIndice` sin usar `heapq`, `deque` ni `set` [FR-CAZ-06, FR-CAZ-14]

**Checkpoint**: Modelos de datos y módulos algorítmicos listos. Se desbloquea la implementación de las historias de usuario.

---

## Phase 3: User Story 1 - Costos de terreno en salidas y tiempos de tránsito (Priority: P1) 🎯 MVP

**Goal**: Implementar costos de tránsito diferenciados en salidas ($\ge 1$, default 100, simétrico) y cálculo universal de intervalo de desplazamiento `max(1, costo_salida * 100 // velocidad)` con reescalado dinámico según P1 §2.3.

**Independent Test**: Verificar mediante pruebas unitarias la duración de movimientos con distintas velocidades y costos sin enemigos cazadores, incluyendo salidas de costo 1 y reescalado de velocidad.

### Tests for User Story 1 (TDD - Escribir primero y verificar fallo inicial) ⚠️

- [X] T008 [P] [US1] Escribir pruebas unitarias en `tests/test_terreno_cazador.py` para costo predeterminado 100, costo explícito y simetría bidireccional (`test_costo_salida_default_y_simetria`) [FR-CAZ-01]
- [X] T009 [P] [US1] Escribir prueba unitaria en `tests/test_terreno_cazador.py` para Apéndice B Caso 6: actor con velocidad alta (300) atravesando salida de costo 1 con intervalo resultante $\ge 1$ tick virtual (`test_actor_rapido_costo_minimo_intervalo_al_menos_uno`) [FR-CAZ-02]
- [X] T010 [P] [US1] Escribir prueba unitaria en `tests/test_terreno_cazador.py` para Apéndice B Caso 7: reescalado proporcional del tiempo restante de movimiento al cambiar la velocidad durante el cruce de una salida costosa según P1 §2.3 (`test_actor_reescalado_velocidad_en_salida_costosa`) [FR-CAZ-12]
- [X] T011 [P] [US1] Escribir pruebas unitarias en `tests/test_terreno_cazador.py` para universalidad de costos en desplazamientos de errantes y rastreadores y conservación de costos de atacar y esperar (`test_errante_rastreador_costos_transito`) [FR-CAZ-03]

### Implementation for User Story 1

- [X] T012 [US1] Modificar `intentar_mover` y la resolución de desplazamiento en `src/controller2/movimiento.py` para programar el turno del jugador usando el costo de la salida atravesada `salida.costo` en lugar del valor fijo 100 [FR-CAZ-02]
- [X] T013 [US1] Modificar `turno_enemigo` y activación en `src/controller2/enemigos.py` para que los desplazamientos de errantes y rastreadores programen su siguiente turno con intervalo `max(1, costo_salida * 100 // velocidad)` [FR-CAZ-03]
- [X] T014 [US1] Conectar en `src/controller2/reloj.py` y `src/controller2/fachada.py` el cálculo de intervalo y la función `reescalar` al transitar por salidas con costo diferenciado [FR-CAZ-02, FR-CAZ-12]

**Checkpoint**: User Story 1 completamente funcional y validada de forma aislada.

---

## Phase 4: User Story 2 - Persecución estratégica del enemigo cazador (Priority: P1)

**Goal**: Implementar el enemigo «cazador» con rango de costo que en su turno prioriza: (1) ataque si comparte sala, (2) cálculo de ruta de menor costo $d$ a través de salidas abiertas, (3) espera de costo 100 si no hay ruta o $d > \text{rango}$, (4) avance de un paso por la ruta óptima si $d \le \text{rango}$ consumiendo el costo de la salida.

**Independent Test**: Simular en pruebas unitarias partidas con cazadores a diferentes distancias de costo del jugador, comprobando ataque inmediato, espera por rango/bloqueo y avance de un paso.

### Tests for User Story 2 (TDD - Escribir primero y verificar fallo inicial) ⚠️

- [X] T015 [P] [US2] Escribir prueba unitaria en `tests/test_terreno_cazador.py` para Apéndice B Caso 1: cazador sin ruta abierta hacia el jugador permanece en su sala y espera con costo 100 (`test_cazador_sin_ruta_abierta_espera`) [FR-CAZ-05, FR-CAZ-07]
- [X] T016 [P] [US2] Escribir prueba unitaria en `tests/test_terreno_cazador.py` para Apéndice B Caso 2: cazador cuya ruta más barata supera su rango ($d > \text{rango}$) espera con costo 100 (`test_cazador_distancia_mayor_que_rango_espera`) [FR-CAZ-05, FR-CAZ-07]
- [X] T017 [P] [US2] Escribir prueba unitaria en `tests/test_terreno_cazador.py` para Apéndice B Caso 3: cazador prefiere ruta de mayor número de salas pero menor costo total acumulado $d$ frente a ruta con menos salas pero mayor costo (`test_cazador_prefiere_menor_costo_que_menos_salas`) [FR-CAZ-05, FR-CAZ-08]
- [X] T018 [P] [US2] Escribir prueba unitaria en `tests/test_terreno_cazador.py` para caso frontera: cuando el costo mínimo es exactamente igual al rango ($d == \text{rango}$), el cazador avanza un paso (`test_cazador_frontera_d_igual_rango_se_mueve`) [FR-CAZ-05, FR-CAZ-07, FR-CAZ-08]
- [X] T019 [P] [US2] Escribir prueba unitaria en `tests/test_terreno_cazador.py` para combate directo cuando el cazador comparte sala con el jugador al inicio de su turno según P1 §2.8 (`test_cazador_comparte_sala_ataca_directo`) [FR-CAZ-05]
- [X] T020 [P] [US2] Escribir prueba unitaria en `tests/test_terreno_cazador.py` verificando que el cálculo de $d$ suma obligatoriamente el costo de la salida final que ingresa a la sala actual del jugador (`test_costo_total_incluye_salida_final_al_jugador`) [FR-CAZ-05, FR-CAZ-06]
- [X] T021 [P] [US2] Escribir prueba unitaria en `tests/test_terreno_cazador.py` para cazador y jugador en salas contiguas con puerta cerrada: no ataca cuerpo a cuerpo y toma un desvío abierto o espera si no hay camino viable (`test_cazador_vecino_puerta_cerrada_desvio_o_espera`) [FR-CAZ-05, FR-CAZ-10]

### Implementation for User Story 2

- [X] T022 [US2] Implementar en `src/controller2/rutas.py` la función `dijkstra_acotado(estado, origen, destino, rango_max)` utilizando `MonticuloMinimo` y `TablaIndice` para explorar salidas abiertas sin usar `heapq`, `deque` ni `set` [FR-CAZ-06, FR-CAZ-08, FR-CAZ-10]
- [X] T023 [US2] Implementar en `src/controller2/enemigos.py` la función `decidir_accion_cazador(estado, instancia_id, catalogo)` evaluando en orden estricto: ataque cuerpo a cuerpo, cálculo de $d$, espera con costo 100, o avance de un paso con costo de salida [FR-CAZ-04, FR-CAZ-05, FR-CAZ-07, FR-CAZ-08]
- [X] T024 [US2] Integrar el despacho del comportamiento `"cazador"` en `turno_enemigo` de `src/controller2/enemigos.py` y `src/controller2/fachada.py`, ejecutando el ataque o el desplazamiento programado [FR-CAZ-05, FR-CAZ-07, FR-CAZ-08]

**Checkpoint**: User Story 2 completamente funcional y validada de forma aislada.

---

## Phase 5: User Story 3 - Determinismo, equivalencia observable y desempate estricto (Priority: P2)

**Goal**: Garantizar que ante múltiples rutas de costo mínimo el cazador desempate invariablemente eligiendo la sala vecina de menor `id`, reaccione dinámicamente a cambios de puertas y del jugador con equivalencia observable absoluta con un cálculo desde cero, ignore niebla y descarga de salas, y exponga costos y distinción visual en `FotoEstado`.

**Independent Test**: Configurar mapas con caminos simétricos de igual costo y verificar que la vecina elegida coincida siempre con el menor identificador entero; modificar puertas entre turnos y validar equivalencia con recálculo desde cero.

### Tests for User Story 3 (TDD - Escribir primero y verificar fallo inicial) ⚠️

- [X] T025 [P] [US3] Escribir prueba unitaria en `tests/test_terreno_cazador.py` para Apéndice B Caso 4: desempate estricto por menor `id` entre salas vecinas que inician rutas de costo total mínimo idéntico (`test_cazador_desempate_menor_id`) [FR-CAZ-09]
- [X] T026 [P] [US3] Escribir prueba unitaria en `tests/test_terreno_cazador.py` para Apéndice B Caso 5: puerta que se cierra entre turnos del cazador provocando una decisión idéntica a la obtenida con un cálculo completo desde cero en ese instante (`test_cazador_reaccion_puerta_cerrada_entre_turnos`) [FR-CAZ-10, FR-CAZ-11]
- [X] T027 [P] [US3] Escribir prueba unitaria en `tests/test_terreno_cazador.py` verificando que una puerta con evento de cierre automático pendiente en la agenda se considera abierta y transitable en el instante actual (`test_puerta_con_cierre_pendiente_es_transitable`) [FR-CAZ-06, FR-CAZ-11]
- [X] T028 [P] [US3] Escribir prueba unitaria en `tests/test_terreno_cazador.py` validando que el cazador conoce el esqueleto completo y puertas sin verse restringido por niebla de guerra ni descarga de salas (`test_cazador_ignora_niebla_y_descarga`) [FR-CAZ-10]
- [X] T029 [P] [US3] Escribir prueba unitaria en `tests/test_terreno_cazador.py` verificando que `FotoEstado` contiene los costos de cada salida de la sala actual y que el cazador se distingue en la lista de enemigos (`test_vista_muestra_costos_y_cazador`) [FR-CAZ-13]

### Implementation for User Story 3

- [X] T030 [US3] Implementar en `src/controller2/rutas.py` y `src/controller2/enemigos.py` la regla de selección determinista $\min_{v \in V^*} v.\text{id}$ entre las vecinas óptimas sin depender del orden de inserción ni usar `set` [FR-CAZ-09]
- [X] T031 [US3] Modificar `abrir_puerta` y `ejecutar_cierre` en `src/controller2/movimiento.py` e `src/controller2/fachada.py` para incrementar `estado.puertas_version += 1` cada vez que cambia el estado de una puerta [FR-CAZ-11]
- [X] T032 [US3] Implementar en `src/controller2/enemigos.py` la estructura `RutaCazador` y la política de invalidación de caché (invalidar si `sala_jugador` cambia o `puertas_version` no coincide), garantizando equivalencia observable absoluta [FR-CAZ-11]
- [X] T033 [US3] Actualizar `foto()` en `src/controller2/fachada.py` y el renderizado en `src/view/capas.py` y `src/view/sprites.py` para visualizar costos en salidas e identificar visualmente a los enemigos cazadores [FR-CAZ-13]

**Checkpoint**: User Story 3 completamente funcional y validada de forma aislada.

---

## Phase 6: User Story 4 - Escalabilidad y fluidez del ciclo de eventos (Priority: P2)

**Goal**: Asegurar que el ciclo de eventos del motor se resuelva en $\le 20\text{ ms}$ con 50 cazadores activos, que los cálculos con rango pequeño se acoten a la región dentro del rango y no al tamaño de la cripta, y proveer la suite comparativa en `--bench`.

**Independent Test**: Ejecutar micro-benchmarks midiendo tiempos de procesamiento con decenas de cazadores en criptas de 10 a $10\,000$ salas y contrastar con los umbrales de éxito SC-CAZ-01 y SC-CAZ-02.

### Tests for User Story 4 (TDD - Escribir primero y verificar fallo inicial) ⚠️

- [X] T034 [P] [US4] Escribir prueba de rendimiento en `tests/test_terreno_cazador.py` validando que el ciclo de eventos con 50 cazadores activos tome $\le 20\text{ ms}$ (`test_rendimiento_ciclo_cazadores_menos_20ms`) [FR-CAZ-14]
- [X] T035 [P] [US4] Escribir prueba de rendimiento en `tests/test_terreno_cazador.py` verificando que para rango pequeño ($R=200$) el tiempo de decisión en cripta de $10\,000$ salas no crezca proporcionalmente al mapa y permanezca $< 1.0\text{ ms}$ (`test_rendimiento_rango_pequeno_independiente_tamano_cripta`) [FR-CAZ-14]
- [X] T036 [P] [US4] Escribir prueba unitaria en `tests/test_terreno_cazador.py` para la ejecución íntegra y sin errores de la suite de cazadores de `--bench` (`test_bench_suite_cazador_ejecucion`) [FR-CAZ-15]

### Implementation for User Story 4

- [X] T037 [US4] Implementar poda por rango en `src/controller2/rutas.py` descartando la expansión de salas con costo tentativo $> \text{rango}$, acotando el cálculo a la bola local $B(u, \text{rango})$ [FR-CAZ-14]
- [X] T038 [US4] Implementar en `src/orchestrator/bench.py` la función `bench_cazadores()` cubriendo los 5 ejes obligatorios: 1 vs 50 cazadores, rango pequeño vs grande, cálculo individual vs compartido, reutilización de ruta vs recálculo total, y puertas estables vs inestables [FR-CAZ-15]
- [X] T039 [US4] Conectar la suite `bench_cazadores()` a `correr_todo()` en `src/orchestrator/bench.py` y a la opción CLI `--bench` en `src/main.py` [FR-CAZ-15]

**Checkpoint**: User Story 4 completamente funcional y validada.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Verificación global de calidad, cumplimiento de restricciones algorítmicas, regresión general y documentación.

- [X] T040 [P] Ejecutar auditoría estricta de código mediante script en `src/` asegurando ausencia absoluta de `import heapq`, `from heapq`, `deque` y `set` en todo el código nuevo de la capacidad [FR-CAZ-14]
- [X] T041 Ejecutar la suite completa de pruebas de regresión del repositorio con `pytest tests/ -q` confirmando 100% de éxito sin degradación en capacidades preexistentes [FR-CAZ-01 a FR-CAZ-15]
- [X] T042 Ejecutar y verificar todos los comandos y escenarios descritos en `specs/001-terreno-cazador/quickstart.md`
- [X] T043 [P] Registrar en `PROMPTS_LLM.md` la sesión de prompts y respuestas asociada a la generación de tareas de la capacidad 001 conforme al Principio VII de la Constitución

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup
     │
     ▼
Phase 2: Foundational (Blocking Prerequisites: T003 - T007)
     │
     ├───────────────────────┬───────────────────────┐
     ▼                       ▼                       ▼
Phase 3: US1 (P1) 🎯    Phase 4: US2 (P1)       Phase 5: US3 (P2)
(Terreno e intervalos)  (Persecución Cazador)   (Determinismo/Equiv.)
     │                       │                       │
     └───────────────────────┼───────────────────────┘
                             ▼
                    Phase 6: US4 (P2)
                 (Escalabilidad & --bench)
                             │
                             ▼
                    Phase 7: Polish
```

- **Setup (Phase 1)**: Sin dependencias, arranca inmediatamente.
- **Foundational (Phase 2)**: Depende de Phase 1. Bloquea todas las historias de usuario.
- **US1 (Phase 3)**: Depende de Phase 2. Puede ejecutarse en paralelo con US2 y US3 o secuencialmente.
- **US2 (Phase 4)**: Depende de Phase 2 y utiliza los modelos de salida de US1.
- **US3 (Phase 5)**: Depende de Phase 2 y complementa las decisiones de US2 con desempate e invalidación de caché.
- **US4 (Phase 6)**: Depende de US1, US2 y US3 completas para medir el motor integrado.
- **Polish (Phase 7)**: Depende de todas las fases anteriores.

### Within Each User Story

- TDD estricto: Las tareas de pruebas deben implementarse y fallar antes de comenzar la implementación.
- Modelos antes de servicios/algoritmos.
- Algoritmos antes de integración con el motor y la fachada.

---

## Parallel Opportunities

- **Fase 1**: `T002` puede desarrollarse en paralelo con `T001`.
- **Fase 2**: `T003`, `T004`, `T005`, `T006`, y `T007` tocan archivos distintos y pueden desarrollarse en paralelo.
- **Fase 3 (US1)**: `T008`, `T009`, `T010`, y `T011` pueden escribirse en paralelo.
- **Fase 4 (US2)**: `T015`, `T016`, `T017`, `T018`, `T019`, `T020`, y `T021` pueden escribirse en paralelo.
- **Fase 5 (US3)**: `T025`, `T026`, `T027`, `T028`, y `T029` pueden escribirse en paralelo.
- **Fase 6 (US4)**: `T034`, `T035`, y `T036` pueden escribirse en paralelo.
- **Fase 7**: `T040` y `T043` pueden ejecutarse en paralelo.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Completar Phase 1: Setup.
2. Completar Phase 2: Foundational (requisito bloqueante).
3. Completar Phase 3: User Story 1 (costos de salida e intervalos).
4. **Validar MVP**: Ejecutar `pytest tests/test_terreno_cazador.py -k "costo or intervalo"` para confirmar que la base física y temporal del terreno opera al 100%.

### Incremental Delivery

1. Setup + Foundational -> Cripta con soporte de costos de salida y fichas de cazador.
2. User Story 1 -> Actores transitan salidas según costo y reescalan su tiempo virtual.
3. User Story 2 -> Cazadores persiguen al jugador por ruta óptima, atacan o esperan por rango.
4. User Story 3 -> Desempate estricto por menor `id`, invalidación de rutas y visualización en interfaz.
5. User Story 4 -> Poda por rango, ciclo $\le 20\text{ ms}$ y suite `--bench`.
6. Polish -> Auditoría de estructuras (`heapq`/`deque`/`set` = 0), regresión y registro en `PROMPTS_LLM.md`.

## Phase 8: Convergence

Revisión 2026-11-16: checklist de requisitos 16/16; sin hooks registrados.

- [X] T044 Corregir regresión de validación estricta de tipos y comparador realmente enlazado sin pop(0); añadir auditoría y ejecutar regresión por FR-CAZ-01/FR-CAZ-14 y Constitución III/V (contradicts).
- [ ] T045 Probar y corregir búsqueda individual acotada desde cazador, desempates propagados y descarte de entradas obsoletas por FR-CAZ-09/FR-CAZ-14 y plan: cálculo individual (partial).
- [ ] T046 Probar e integrar esqueleto compartido con 003, puertas vivas y tránsito por salas descargadas sin contenido ni niebla por FR-CAZ-10/FR-CAZ-11 (partial).
- [ ] T047 Medir y optimizar ciclo completo real de 50 cazadores, búsqueda local con jugador distante y benchmark sin caché accidental por SC-CAZ-01/SC-CAZ-02/FR-CAZ-15 (partial).
- [ ] T048 Validar costos/cazadores con deshacer, guardado, replay y receptor de historia 004; actualizar evidencia y registros por FR-CAZ-11 y Constitución IV/V/VII (partial).
