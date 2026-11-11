# Tasks: Línea de tiempo (004)

**Input**: Diseño en `specs/004-linea-de-tiempo/`.
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/interfaces.md`.
**Tests**: incluidos porque los escenarios de aceptación y la Constitución V requieren evidencia funcional.

## Phase 1: Preparación

- [X] T001 Revisar disponibilidad del enunciado íntegro P2 y actualizar `specs/004-linea-de-tiempo/research.md`. Completada2026-11-10: contraste con `docs/Cripta Parte II.md`, §§3.6,5.5,6.1–6.3 y Apéndice B; aclaraciones locales separadas de requisitos oficiales. No implica aceptación funcional.
- [X] T002 Obtener aprobación explícita del receptor histórico C2–orquestador propuesto en `specs/004-linea-de-tiempo/contracts/interfaces.md` y registrar acuerdo/versión en `CONTRATOS.md`; no editar contratos compartidos antes de esa aprobación.
- [X] T003 Confirmar el nuevo formato de guardado con versión distinta a v1/v2/v3 y la política de rechazo en `CONTRATOS.md` y `specs/004-linea-de-tiempo/contracts/interfaces.md`; preserva los lectores técnicos previos sin carga silenciosa en P2.

## Phase 2: Fundamentos compartidos

- [X] T004 Crear `src/models/historia.py` con DTO inmutable de resumen histórico para reloj, sala, estadísticas, inventario, efectos, enemigos locales y mapa conocido; sus colecciones no deben exponer referencias al estado activo.
- [X] T005 Crear `src/controller2/linea_tiempo.py` con las entidades del modelo de `specs/004-linea-de-tiempo/data-model.md`: registros inversos, cortes de acción/tiempo, checkpoints inicial/luego cada K y validación de K entero ≥1; almacenar en orden cronológico sin snapshot por acción.
- [X] T006 Extender `src/controller2/linea_tiempo.py` con índice temporal en lista cronológica y búsqueda binaria propia para el primer corte de decisión en t; no usar `sorted()`, `list.sort()` ni dict como índice.
- [X] T007 Añadir serialización/deserialización validada de línea y checkpoints en `src/controller2/linea_tiempo.py`, incluyendo K, ordinal vigente, cortes, deltas y posiciones de checkpoint; rechazar secuencias, rangos o intervalos inválidos.
- [X] T008 Crear `tests/test_linea_tiempo.py` para K inválido, registros ordenados, checkpoints inicial/cada K, cortes por acción y tiempo, tiempos empatados, repetición tras truncamiento y rechazo de datos serializados malformados.

## Phase 3: User Story 1 — Consultar la línea vigente (P1)

**Goal**: consultar estado por tiempo o acción, con checkpoints/deltas, replay y guardado, sin mutar partida ni el retroceso P1.
**Independent test**: con fixtures offline, comparar todos los campos del resumen con estados esperados; verificar que reloj, RNG, agenda, inventario, mapa, log y pila P1 no cambian por consulta.

### Pruebas del recorrido

- [X] T009 [P] [US1] Crear `tests/test_historia.py` para consulta inicial, t intermedio/actual/futuro/negativo/no entero, #k válido/inexistente, eventos automáticos empatados y resumen con los campos mínimos de FR-LIN-03.
- [X] T010 [P] [US1] Verificar en `tests/test_historia.py` para cobertura de deltas de todos los eventos/jugadas, incluyendo efectos, enemigos, RNG, agenda, puertas, trampas y conocimiento; consulta histórica no debe mutar el estado activo.
- [X] T011 [P] [US1] Verificar en `tests/test_historia.py` para retroceso que trunca acciones/checkpoints revertidos, conserva P1 en tope cinco, renumera la rama, cuenta cada paso de viaje y agrega el pergamino al ordinal 004 sin cambiar contadores/exclusiones P1.
- [X] T012 [P] [US1] Verificar en `tests/test_historia.py` para roundtrip de registros/checkpoints v4, corrupción/índices/rangos, preservación de sesión al fallar y rechazo explícito de v1/v2 P1 y v3 P2 sin historia.
- [X] T013 [P] [US1] Verificar en `tests/test_historia.py` para `historia <t>`/`historia #k`, consultas sin tiempo/log/drenaje, línea reconstruida idéntica, y estado del juego/PilaDeshacer intactos.
- [X] T014 [P] [US1] Verificar en `tests/test_historia.py` y `tests/test_cli_historia.py` el replay con acciones de viaje y deshacer, igualdad de resumen a tiempo t, final anticipado cuando t supera el reloj final y manejo de incompatibilidad/corrupción.
- [X] T015 [P] [US1] Añadir `tests/test_cli_historia.py` para `--checkpoint-cada K` (K≥1), `--replay ... --hasta t`, rechazo de argumentos inválidos y salida idéntica al resumen interactivo sin crear Pygame.

### Registro de cambios e integración

- [X] T016 [US1] Auditar en `src/controller2/fachada.py`, `src/controller2/efectos.py`, `src/controller2/movimiento.py`, `src/controller2/enemigos.py` y `src/controller2/deshacer.py` cada mutación/evento para encontrar cambios que no produzcan una inversa cronológica completa; documentar la matriz de operaciones en `specs/004-linea-de-tiempo/research.md`.
- [X] T017 [US1] Integrar el receptor 004 en `src/controller2/fachada.py` usando solo el contrato aprobado: emitir cada inversa en orden causal, incluyendo eventos automáticos, y truncar los cambios de intervalos revertidos sin tocar el colector de conocimiento 002.
- [X] T018 [US1] Integrar en `src/orchestrator/sesion.py` inicio/fin de decisión y cierre de drenaje; contar acciones aceptadas que cambian la partida, cada paso automático y el pergamino acordado, y crear checkpoint al completar K acciones.
- [X] T019 [US1] Implementar reconstrucción en `src/controller2/linea_tiempo.py` desde checkpoint posterior sobre estado/agenda aislados, aplicando como máximo K intervalos inversos; jamás ejecutar HTTP, motor vivo o vista durante consulta.
- [X] T020 [US1] Exponer `Sesion.historia(t)` y `Sesion.historia_accion(k)` en `src/orchestrator/sesion.py`, producir `ResumenHistorico` en `src/models/historia.py` y asegurar que tiempo, inventario y conocimiento pertenecen al corte consultado.
- [X] T021 [US1] Añadir parseo y render del comando `historia <t|#k>` en `src/orchestrator/consola.py`; consultas, futuro/rechazo y errores no deben pasar por la ruta genérica que drena tiempo.
- [X] T022 [US1] Añadir `--checkpoint-cada K` y `--hasta T` en `src/controller1/cli.py`; validar enteros y propagar configuración/consulta a `src/main.py` y `src/orchestrator/sesion.py`.
- [X] T023 [US1] Extender `Sesion.reproducir()` en `src/orchestrator/sesion.py` y el modo replay de `src/main.py` para reconstruir hasta t e imprimir el mismo DTO sin iniciar `VistaApp`; para t posterior al final, imprimir estado final y aviso de final anticipado.
- [X] T024 [US1] Extender `src/controller1/savegame.py` y carga candidata de `src/orchestrator/sesion.py` para el nuevo formato v4 con línea completa; rechazar v1/v2/v3 sin tocar sesión ni viaje actuales, validar referencias antes de instalar y no reanudar automáticamente.
- [X] T025 [US1] Extender `src/orchestrator/bench.py` y `correr_todo` para generar 5 000+ acciones sintéticas, ejecutar 100 calentamientos y medir 1 000 consultas para al menos K=10/20/50 más alternativa sin checkpoints: mediana/p95/máximo, bytes y cantidad de deltas aplicados, sin red ni render.
- [X] T026 [US1] Ejecutar las mediciones de T025, elegir el default K solo con evidencia y registrar carga, máquina, resultados y límites en `DECISIONES.md`; confirmar FR-LIN-13 cuando el máximo observado en las 1 000 consultas medidas sea ≤50 ms, y FR-LIN-14, o documentar el incumplimiento sin afirmar éxito.
- [X] T027 [US1] Actualizar `specs/004-linea-de-tiempo/quickstart.md` con resultados ejecutados de escenarios 1–7, determinismo, compatibilidad, benchmarks y limitaciones; no marcar escenarios que solo existan en fixtures como recorrido manual.

## Phase 4: Pulido y verificación cruzada

- [X] T028 Revisar `specs/004-linea-de-tiempo/tasks.md`, `spec.md`, `plan.md` y `research.md` para trazabilidad completa de FR/SC y verificar el contraste P2 ya registrado; mantener pendiente la aceptación contractual y la evidencia funcional/de rendimiento que aún falten.
- [X] T029 Ejecutar regresión `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python -m pytest tests/ -q`; resolver regresiones y registrar resultado/omisiones en `specs/004-linea-de-tiempo/quickstart.md`.
- [X] T030 Registrar prompts, uso y resultados en `PROMPTS_LLM.md`; cerrar solo tareas comprobadas y declarar dependencias reales pendientes de contratos, integración o mediciones; la fuente P2 ya está disponible.

## Interfaz gráfica — alcance solicitado el 2026-11-10

- [X] T031 Auditar patrones de interfaz y atajos en `src/view/app.py`, `ui.py`, `medidas.py`, `paleta.py`, `texto.py` y `entrada.py`; documentar composición y reutilización de componentes para historia. Consolidar tokens de8/16/24/32 px lógicos para espaciados y padding, con esquinas rectas, escalados con Medidas; trazos finos permitidos. No rediseñar otras pantallas. Requisitos: FR-LIN-15, FR-LIN-16. Dep.: T002/T003 antes de cambios compartidos.
- [X] T032 Implementar panel visual de historia con acceso visible, selección por tiempo/acción, navegación anterior/siguiente, foco, teclado/ratón y Escape; resumen jerarquizado y mapa histórico usando DTO de Sesión. Manejar vacíos, errores y contenido largo; suspender movimiento/viaje durante el foco y evitar pasos acumulados al cerrar. Requisitos: FR-LIN-03, FR-LIN-04, FR-LIN-15, FR-LIN-16. Dep.: T020,T031.
- [ ] T033 Probar interacción del panel y ausencia de mutaciones, revisar capturas a1024×800 y tamaños admitidos con nombres/listas largos, y ejecutar recorrido manual de apertura/navegación/consulta inválida/cierre. Registrar capturas/resultados y omisiones en quickstart.md; completar ayuda de interfaz en README.md. Requisitos: FR-LIN-15, FR-LIN-16. Dep.: T032. El cierre T027–T030 requiere también esta evidencia.

## Dependencias

```text
T001,T002,T003 → T004–T008 → US1 T009–T015
T008 + aceptación T002/T003 → T016 → T017 → T018
T004–T008 → T019 → T020 → T021,T022 → T023
T018,T019 → T024
T018–T024 → T025 → T026
T009–T026 → T027 → T028–T030
```

T016/T017 comparten C2 y se serializan. T009–T015 pueden escribirse en archivos
distintos tras los fundamentos; T021/T022 no modifican el mismo archivo y pueden
avanzar en paralelo después de T020. No empezar T017 ni cambios de contratos
antes de la aceptación T002/T003.

## Parallel opportunities

- T004–T006 comparten `linea_tiempo.py`; ejecutar en secuencia aunque las pruebas
  de DTO y parser de CLI sean independientes.
- T009, T010, T012, T014 y T015 usan archivos distintos y pueden prepararse en
  paralelo tras acordar los contratos; T011/T013 son suites diferentes pero
  dependen del protocolo de truncamiento.
- T021 y T022 pueden desarrollarse en paralelo tras el API de Sesión T020.
- No paralelizar los cambios de `fachada.py`, `deshacer.py` y `sesion.py`: su
  orden causal y frontera de intervalos deben revisarse juntos.

## Implementation strategy

MVP de US1: line model + deltas/checkpoints + consulta sin mutación por tiempo y
acción; después CLI interactiva. Segunda entrega: guardar/cargar v4 y replay.
Último cierre: rendimiento, K por defecto, regresión y contraste de P2. No iniciar
la implementación del receptor hasta aprobar el contrato compartido.

## Corte de implementación — 2026-11-10

**32/33 tareas completadas.** T001–T032 verificadas; T033 parcialmente ejecutada:
pruebas de interacción/cuatro tamaños/contenido largo y capturas reales offline
completas, pero falta el recorrido manual humano en ventana. Se conserva su
casilla abierta. No se declara aceptación humana ni cierre académico total.

Regresión464 aprobadas/1 omitida; benchmark de5.000 órdenes del motor real con
K10/20/50 y sin checkpoints intermedios. K20 por defecto: máximo2,862450 ms en
1000 consultas tras100 calentamientos; contador observado≤20 acciones. Tabla,
memoria, carga y límites en DECISIONES.md e informes JSON. Evidencias FR-LIN-01–16
y los siete escenarios en quickstart.md.

La revisión inicial de consistencia detectó que el receptor propuesto004 no era
el aprobado002 y que las inversas P1 no cubrían toda la historia. Se concretó
y aprobó el contrato separado antes del código, se conservó P1 y se documentó
la captura por escrituras. Revisión final: requisitos funcionales, pruebas y
mediciones trazados; única aceptación pendiente de004 es el recorrido humano
T033. La integración futura con001 y el§5.6 transversal no se adjudican a004.
