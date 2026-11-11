# Research: Línea de tiempo (004)

## Estado de fuentes

- `specs/004-linea-de-tiempo/spec.md` es la fuente funcional de este plan.
- Fuente normativa disponible: [Cripta Parte II](../../docs/Cripta%20Parte%20II.md), §§3.6, 5.5, 6.1–6.3 y Apéndice B. La guía de división del trabajo es complementaria. Contraste documental realizado el 2026-11-10; no implica implementación ni aceptación ejecutada.
- La implementación parte de la base existente en la rama `main`; `specs/004-linea-de-tiempo` es carpeta de capacidad, no una rama Git dedicada.

## Decisiones

### Reconstrucción histórica con deltas inversos y checkpoints

**Decisión**: reutilizar las entradas inversas de C2 como cambios históricos cronológicos, y conservar checkpoints completos separados por K acciones aceptadas. Para consultar un punto anterior, trabajar sobre una copia aislada del checkpoint posterior más cercano y aplicar las inversas en orden inverso hasta el corte solicitado. Conservar un checkpoint inicial y crear los siguientes al cerrar cada intervalo de K acciones.

**Evidencia local**: `src/controller2/deshacer.py` ya modela cambios reversibles por evento y `aplicar_inversa(estado, agenda, inversa)` restaura C2 sin copiar el estado por acción. `src/controller2/fachada.py` concentra `Fachada._apilar` para registrar inversas y `Fachada.deshacer` para truncar el último intervalo. `EstadoPartida.a_dict()/desde_dict()` serializa el estado requerido por un checkpoint. Las inversas existentes solo alimentan una pila limitada a cinco intervalos, así que la línea necesita su propio almacenamiento sin ese límite.

**Alternativas consideradas**:

- Copia completa por acción: descartada porque contradice FR-LIN-10 y hace crecer memoria según tamaño del estado por acción.
- Reproducir desde el inicio para cada consulta: descartada porque no garantiza como máximo K acciones de reconstrucción ni el límite de 50 ms.
- Guardar solo el último estado y deltas hacia delante: no basta para consultas anteriores y no reutiliza la operación inversa ya probada por el motor.

**Condición de diseño**: todas las mutaciones relevantes, incluidos eventos automáticos, deben producir inversas completas y ordenadas. La implementación debe auditar cada ruta de escritura a C2; cualquier mutación que no pase por `_apilar` requiere integración explícita. El conteo de consultas se medirá en acciones jugador, y también se reportará el número de eventos inversos aplicados por intervalo.

La guía oficial de P1 §2.11 excluye el uso/consumo del pergamino del historial reversible y del contador de acciones del juego. La aclaración del jugador para 004 define un ordinal separado de la línea de tiempo: el pergamino cuenta en `historia #k`/K aunque la pila de deshacer de P1 no lo cuente ni revierta su consumo. No cambiar `EstadoPartida.acciones_jugador` ni la semántica P1 para conseguirlo.

### Índice temporal y acciones numeradas

**Decisión**: almacenar los registros en orden de ejecución y etiquetarlos con reloj virtual, fase/orden dentro del instante y ordinal de acción vigente. En la rama vigente, los tiempos son no decrecientes: al usar un pergamino se trunca la rama revertida y se continúa desde el reloj restaurado, por lo que puede repetirse un tiempo pero no se conserva el tramo de reloj futuro eliminado. Mantener los cortes de tiempo en una lista cronológica y resolver el primer punto de decisión en `t` con búsqueda binaria propia; no ordenar los registros ni usar `sorted()`. `historia <t>` queda después de eventos automáticos con tiempo ≤t y antes de la primera decisión del jugador en t; `historia #k` localiza el corte inmediatamente anterior a la acción numerada k. Cada paso de «ir a» y cada uso aceptado del pergamino ocupa su propio ordinal. Al deshacer, se truncan los intervalos revertidos, se renumeran las acciones supervivientes y se agrega el uso del pergamino al final.

**Alternativas consideradas**: usar tiempo como único índice falla cuando se repite tras deshacer; conservar huecos después del retroceso contradice la regla acordada de renumeración; numerar comandos rechazados o consultas contradice FR-LIN-04 y las aclaraciones aceptadas.

### Límite de versión de guardado

**Decisión**: el formato que incluya la línea completa debe distinguirse de v1/v2 P1 y de v3 P2 anterior a 004. La carga P2 de 004 rechazará esos archivos con un error explícito; no sintetizará ni afirmará historia que no está persistida. El número y layout exactos del formato se fijan al diseñar contrato de persistencia, preservando lectores técnicos que aún necesite la suite.

**Evidencia local**: `src/controller1/savegame.py` escribe v3 cuando hay conocimiento P2, expone `cargar_p2()` para validar y permite lectores técnicos de v1/v2. `Sesion.cargar()` prepara un candidato aislado antes de instalarlo, patrón que debe conservarse al validar la historia serializada.

### Integración con replay y consulta

**Decisión**: `Sesion` expone consultas puras por reloj o ordinal y produce un resumen inmutable. El comando `historia` muestra ese resumen sin llamar al camino de intención/drenaje. `--replay ... --hasta t` reutiliza el replay existente, reconstruye la línea vigente y pide el resumen a `Sesion`; si t excede el reloj final, muestra el último estado y la nota de fin anticipado. El replay no crea `VistaApp`.

**Evidencia local**: `src/orchestrator/sesion.py` coordina intención, drenaje, guardado/carga y replay; `src/main.py` deriva `--replay` sin crear la vista. `src/controller1/gamelog.py` conserva líneas opacas y C2 interpreta las acciones.

## Riesgos pendientes para el plan

- Confirmar con pruebas que las inversas capturan todas las mutaciones de eventos, no solo conocimiento ni las acciones cubiertas por el pergamino.
- Guardar/cargar checkpoints e inversas puede aumentar mucho el archivo; el bench deberá medir bytes reales además de tiempo.
- El criterio ≤50 ms aplica al máximo observado de 1 000 consultas tras 100 calentamientos en una partida de 5 000+ acciones con K por defecto. El resultado depende del tamaño del checkpoint y del número de eventos por acción; informar ambos, no solo cantidad de acciones. Mediana y p95 se reportan como diagnósticos.
- El contrato C2–orquestador para el receptor histórico es nuevo y debe revisarse/aprobarse antes de modificarlo, según `CONTRATOS.md` y la constitución.
- El enunciado ya está disponible y contrastado; quedan pendientes implementación, pruebas y mediciones. La carga integrada con cazadores y costos variables de §5.6 espera la entrega de A, pero el desarrollo aislado de004 no la requiere.

## Preparación actualizada — 2026-11-10

| Fuente oficial | Cobertura del diseño |
| --- | --- |
| §3.6: instante tras eventos, consulta por tiempo/acción, pureza y rechazo de futuro | FR-LIN-01–06; T009,T013–T015,T020–T023 |
| §3.6: retroceso elimina acciones; checkpoints configurables y reconstrucción ≤K | FR-LIN-07–11; T005–T008,T011,T018–T019 |
| §3.6: persistencia completa e incompatibilidad explícita | FR-LIN-12; T007,T012,T024 |
| §§5.5/6.1–6.3: cambios + checkpoints, truncamiento eficiente, ≥5000 acciones, ≤50 ms y comparación de tres K | FR-LIN-09–14; T025–T026 |
| Apéndice B: seis casos oficiales de línea de tiempo | Escenarios1–6 de spec.md; T009,T011–T015 |

El escenario7 (rechazar P2 anterior sin historia), el ordinal del pergamino y la
renumeración son acuerdos locales registrados en las aclaraciones, no reglas
adicionales atribuidas al enunciado. Los100 calentamientos y1000 consultas son
el protocolo local de medición; el umbral50 ms y las5000 acciones son oficiales.

La aprobación registrada en CONTRATOS.md corresponde a la propuesta002: lotes
bidireccionales y truncamiento. No equivale a aprobar automáticamente las firmas
distintas propuestas por004 (`registrar_cambio`, `cerrar_accion`,
`truncar_intervalo`) ni el formato v4. T002/T003 siguen pendientes: conciliar
receptor y atomicidad con el contrato vigente, concretar layout/validación y
registrar el acuerdo antes de cambiar interfaces. Esta revisión no solicita
nueva aprobación ni modifica contratos compartidos.

Puede avanzarse con el motor actual y fixtures offline en el modelo histórico,
la auditoría de inversas y las pruebas de004. La integración final deberá cubrir
las mutaciones nuevas de001 cuando A las entregue. §5.6 sigue siendo trabajo
transversal de B y no queda cerrado por preparar004.

## Inspección previa de captura — 2026-11-10

Esta inspección prepara T016; no la cierra ni sustituye sus pruebas de cobertura.

| Ruta existente | Cobertura actual | Trabajo que exige004 |
| --- | --- | --- |
| `Fachada._apilar` | Inversa P1 y deltas de conocimiento002 | Capturar delta histórico completo antes del descarte por tope cinco; mantener receptor002 intacto |
| `_tras_accion` / `_programar_turno_jugador` | Contador, rastro y programación posteriores al apilado | Incluir esos cambios y los seq de agenda en el registro004 |
| `avanzar` | Saca evento y mueve reloj antes de producir la inversa | Registrar también consumo del evento, reloj y secuencia causal; agrupar empates al consultar t |
| `fin_efecto` | Puede reescalar agenda después de `_apilar` | Capturar reprogramación completa, no solo efecto anterior |
| Combate / turnos / oleada | Llamadas RNG y cambios de instancias | Restaurar estado RNG, orden de entidades y agenda; las inversas P1 no garantizan todo ello |
| `aplicar_inversa` | Excluye pergaminos deliberadamente | Historia necesita registrar su adquisición, traslado y consumo sin cambiar undo P1 |
| `Sesion._registrar_vecinas` | Precarga fuera del apilado | Definir captura de altas de salas dormidas sin confundir hidratación con revelación |
| `_ok` / `avanzar` | Actualizan victoria/derrota tras sincronizar | Cerrar registro después de las mutaciones finales |
| `Fachada.deshacer` | Restaura intervalo y emite truncamiento002 | Recortar sufijo004 y agregar consumo de pergamino como ordinal separado |

Hallazgo principal: transmitir las inversas actuales sin ampliarlas produciría
una historia incompleta. La propuesta concreta de contrato y layout v4 está en
`contracts/interfaces.md`; T002/T003 siguen pendientes de aceptación y no se
modifica CONTRATOS.md anticipadamente. No se requiere entrega de A para resolver
esta captura sobre el motor actual.
