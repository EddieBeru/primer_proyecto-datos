# Implementation Plan: Niebla de guerra e «ir a»

**Branch**: capacidad `002-niebla-ir-a`; rama Git real `main`, sin crear rama dedicada | **Date**: 2026-11-06 | **Spec**: [spec.md](spec.md)

**Input**: especificación aclarada en commit `7795927`, con cuatro respuestas aceptadas, y ajustes documentales aceptados tras el análisis del 2026-11-08.

## Summary

Agregar conocimiento explícito del jugador, separado del esqueleto descargado, las salas precargadas y las visitas físicas. Revelar incrementalmente, recordar puertas observadas presencialmente y registrar cambios reversibles. Implementar viaje automático como secuencia cancelable de movimientos ordinarios: C2 decide cada paso con Dijkstra sobre conocimiento; Sesión ejecuta y drena eventos; la vista recupera control antes de continuar.

Este workflow termina en diseño, sin tareas ni código. Decisiones en [research.md](research.md), entidades en [data-model.md](data-model.md), interfaces propuestas en [contracts/interfaces.md](contracts/interfaces.md), validación futura en [quickstart.md](quickstart.md).

## Technical Context

**Language/Version**: Python ≥3.11; intérprete local `.venv`: 3.12.3.

**Primary Dependencies**: pygame-ce y requests existentes; sin nuevas dependencias de ejecución. pytest para pruebas, ausente en `.venv` al planificar.

**Storage**: binario propio C1 actualmente v2; proponer v3 para P2 con índice por sala, core JSON y conocimiento/deltas serializados como registros. No persistir búsquedas ni continuación automática.

**Testing**: pytest con proveedores falsos, SDL dummy para vista; validación documental en esta fase.

**Target Platform**: Linux de escritorio, consola y Pygame; validación offline sin HTTP.

**Project Type**: juego de escritorio con C1, C2, orquestador y vista.

**Performance Goals**: siguiente paso ≤5 ms en mapa de referencia completo; revelación de costo esperado amortizado proporcional a registros de salas/puertas consultados o modificados. Las operaciones ordinarias no barren el mapa conocido; las mediciones incluyen el recorrido de registros durante expansiones del índice. Son objetivos pendientes de medición; separar búsqueda, eventos, red y renderizado.

**Constraints**: estructuras propias; sin `heapq`, `deque`, `set` ni `dict` como índices evaluados; sin `sorted`/`list.sort` en ordenamientos evaluados. `list` como almacenamiento y diccionarios en JSON/DTO mantienen usos permitidos. C2 no importa C1. No snapshots por acción para retroceso. No refactorizar colecciones históricas ajenas a 002.

**Scale/Scope**: hasta cuatro salidas por sala, IDs enteros dispersos; sintéticos de 100/1 000/10 000 salas y referencia offline versionada. Cazadores, resolubilidad e historia con checkpoints permanecen en sus capacidades.

## Constitution Check

Evaluación antes de investigación y después del diseño:

| Principio | Pre | Post | Evidencia y condición |
|---|---|---|---|
| I. Fuentes | Cumple para diseño | Cumple para diseño | Se distingue guía/acuerdos de enunciado oficial P2, todavía ausente. No se certifica cumplimiento académico definitivo. |
| II. Capas/contratos | Cumple | Cumple | Proveedor inyectado y vista→Sesión→C2. Interfaces propuestas, sin modificar acuerdos vigentes; regla 6.3 antes de implementarlas. |
| III. Estructuras | Cumple | Cumple | Hash/heap propios en paquete neutral, Dijkstra sin biblioteca, alternativas en research. |
| IV. Determinismo | Cumple | Cumple | Desempate estable, deltas causales, replay por movimientos y compatibilidad explícita. |
| V. Validación | Cumple | Cumple | Matriz FR, escenarios offline y método de medición; no atribuir ejecuciones inexistentes. |
| VI. Spec Kit | Cumple | Cumple | Spec aclarada/versionada antes de plan; tasks/analyze/implement posteriores. |
| VII. LLM | Cumple | Cumple | Investigación y diseño registrados en PROMPTS_LLM.md. |

Sin excepciones constitucionales. Antes de implementar cambios K1/K2/K3/K5, obtener aceptación del compañero y actualizar CONTRATOS.md según regla 6.3. La condición no impide documentar ahora la propuesta revisable. El contraste con el enunciado íntegro P2 sigue pendiente; no se sustituye por una decisión técnica.

Las aprobaciones se registran por contrato. El primer incremento de conocimiento solo exige K1 aprobado y enmendado; no requiere completar K2/K3/K5. Las demás tareas conservan las condiciones de aprobación indicadas en tasks.md. La aceptación del usuario de estos ajustes documentales no sustituye la aceptación del compañero.

## Project Structure

### Documentation (this feature)

```text
specs/002-niebla-ir-a/
├── spec.md
├── checklists/requirements.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/interfaces.md
└── quickstart.md
```

`tasks.md` se genera después mediante `$speckit-tasks`.

### Source Code (repository root; cambios previstos, no implementados)

```text
src/
├── estructuras/          # nuevo: tabla_indice.py, monticulo_minimo.py
├── algoritmos/rutas.py   # nuevo: Dijkstra con adyacencia inyectada
├── models/              # Exit.costo, coordinado con 001
├── controller1/          # persistencia v3, proveedores falsos por K1/K2
├── controller2/          # conocimiento.py, viaje.py; integrar modelo/fachada/deshacer
├── orchestrator/         # metadatos, pasos, consola, replay, bench
└── view/                 # mapa conocido, selección y cancelación
tests/                   # suites existentes + conocimiento/rutas/viaje
```

**Structure Decision**: estructuras y núcleo de rutas neutrales, sin importar controladores. No mover la tabla hash de C1, acoplada al LRU. Sesión inyecta metadatos; el movimiento normal conserva la carga de contenido.

## Diseño de implementación

### Conocimiento y reversión

- `EstadoPartida` posee `MapaConocido`. Desconocida es ausencia; avistada guarda solo ID; explorada agrega nombre/salidas/costos. No reutilizar `salas_visitadas` ni `SalaViva.visitada`, que significan entrada real y afectan rastro/puntaje.
- Inicializar sala inicial y avistadas antes de la primera decisión. Entrar explora sala y observa puertas locales. Encender antorcha o entrar con ella explora vecinas inmediatas por salidas abiertas/cerradas; sus salidas crean avistadas sin exploración recursiva. Revelación solo consulta metadatos, nunca contenido/fichas/activación.
- Apertura/cierre actualizan memoria si el jugador ocupa un extremo; cambios remotos no la modifican. Observar extremos de origen/destino al cruzar. Las observaciones pertenecen a sus acciones/eventos y ocurren antes de publicar fotos; consultar mapa/foto no modifica estado.
- Mutaciones efectivas generan `CambioConocimiento(antes, despues)` adjunto a la inversa causal. Deshacer en orden inverso dentro del mismo intervalo, sin nuevo marcador de acción ni snapshots. Inicialización no crea acción deshacible.
- Corregir inversa de encendido: restaurar efecto antorcha anterior y eventos reemplazados además del objeto/conocimiento. No cambiar duración/consumo P1 ni exclusión de pergaminos/caché.
- Ofrecer a 004 receptor opcional de cambios bidireccionales, antes de que la pila de cinco descarte intervalos. 002 entrega formato y deltas; 004 implementa archivo histórico/checkpoints. La pila acotada no representa la historia completa.
- La entrega aislada de 002 se verifica con falsos. La aceptación completa de FR-NIE-08 queda pendiente hasta comprobar con 004 el conocimiento histórico antes/después de entrada, antorcha y retroceso, y su conservación al guardar/cargar; esta verificación no implementa 004 dentro de 002.

### Rutas y ejecución

- Dijkstra propio con heap binario y tabla temporal propia, sobre exploradas y puertas recordadas abiertas. Etiqueta `(distancia, primer_vecino_id)`, orden total estable; resultado: costo, vecino y dirección del siguiente paso. Recalcular antes de cada paso; sin caché de rutas en esta versión.
- `ir a <id>` valida sin tiempo, registra comentario y prepara control transitorio. Destino actual termina sin movimiento antes de comprobar enemigos; destino no explorado se rechaza. Si necesita movimiento y hay enemigos vivos en la sala actual, no inicia. Nunca abre puertas.
- Cada avance ejecuta a lo sumo un movimiento ordinario más drenaje. Detectar enemigos al entrar antes de que actúen/mueran y cualquier daño durante el intervalo aunque una curación posterior lo oculte. No depender solo de la foto final.
- Antes de calcular, el conocimiento local ya refleja las observaciones del intervalo anterior. Un bloqueo real actualiza observación/recalcula sin cobrar intento fallido; si no hay ruta, detener. No reintentar indefinidamente la misma puerta. Fallos de carga de contenido durante un cruce detienen con error, sin avanzar reloj por la espera de red; se distinguen de cargar un archivo de partida.
- Tras cada intervalo comprobar fin de partida, daño, enemigos detectados, llegada, cancelación y existencia de ruta antes del siguiente avance. `deshacer` cancela continuación y revierte solo el último intervalo ordinario. Consultar mapa, foto, inventario o ayuda conserva el viaje. Una acción manual lo cancela antes de procesarse; guardar y pausar también lo cancelan. Cargar solo cancela al instalar correctamente la partida; una carga fallida conserva el viaje anterior, incluso al gestionar su error en la interfaz. Una carga válida no reanuda silenciosamente.
- Pygame procesa entradas y teclas sostenidas antes de avanzar, a lo sumo un cruce por actualización y mínimo 150 ms visuales entre cruces. No ejecutar toda la ruta en una llamada ni simular caminar hasta la puerta para generar el movimiento automático. Reposicionar sprite con `en_puerta` para evitar cruce accidental al devolver control. La espera visual no consume tiempo virtual.

### Integraciones

- Interfaces propuestas en `contracts/interfaces.md`; no modificar CONTRATOS.md durante este workflow.
- 001 es dueño de costo entero≥1/default100, simetría y duración `max(1,costo*100//velocidad)`. B consume esos campos; no duplica fórmula ni implementa cazadores. Falsos ponderados permiten pruebas aisladas; aceptación integrada depende de 001.
- Núcleo neutral disponible para A, sin obligarle a adoptar búsqueda/rango de B. No compartir resultados entre grafo vivo y conocimiento. Se elige implementar el núcleo porque todavía no existe Dijkstra reutilizable.
- K2 propuesto: v3, acceso indexado por sala, conocimiento y deltas; rechazar v1/v2 en flujo P2 explícitamente. Validar cargas normales/en frío en estado candidato antes de sustituir la sesión activa. Coordinar ampliación de 004 sin afirmar historia completa en 002.
- K3 propuesto: `#ir-a <id>` reconocido e ignorado por todos los reproductores; no ejecutar de nuevo la orden automática. Cada paso queda como movimiento e intervalo ordinario.

## Validation Strategy

| Requisitos | Validación prevista |
|---|---|
| FR-NIE-01–07,09 | Inicialización, tres estados, observación local/remota, antorcha, precarga que no revela, mapa sin contenido remoto. |
| FR-NIE-08,17 | Undo entrada/encendido/cierre, conocimiento previo, tope cinco/exclusiones, guardado v3 y deltas para 004. Aceptación completa de FR-NIE-08 condicionada a prueba integrada con 004 (T052). |
| FR-NIE-10–15 | Destino inválido/actual, ponderación/desempate, recálculo, enemigos vivos/dormidos/muertos, daño seguido de curación, ninguna apertura automática. |
| FR-NIE-16,18,21 | Replay ignora comentarios; pasos individuales, motivos, cancelación Pygame/consola sin tiempo, cruce manual conservado. |
| FR-NIE-19–20 | Mediana/p95/máximo de consultas y búsqueda; referencia completa ≤5 ms para cálculo; contar registros tocados al revelar con mapas crecientes e incluir expansiones al medir costo amortizado. |

Ejecutar escenarios 1–11 de spec y regresiones de Sesión/vista/guardado/bitácora. Ver quickstart. No se ejecutaron pruebas de producto ni benchmarks: `.venv` carece de pytest. Esta entrega se valida mediante consistencia documental, enlaces, trazabilidad y ausencia de placeholders.

## Complexity Tracking

Sin excepciones. Hash: acceso esperado O(1), expansión amortizada; las mediciones de revelación incluyen rehash. Dijkstra: O((Vκ+Eκ) log(1+Eκ)) tiempo y O(Vκ+Eκ) memoria en la región conocida descubierta. Extraer registros del mapa conocido cuesta O(Vconocido+Econocido); construir la proyección ordenada por ID mediante mergesort cuesta O(Vconocido log Vconocido+Econocido). La vista reutiliza la proyección mientras el panel esté abierto y no cambie la revisión del conocimiento, sin reconstruirla en cada foto ordinaria. La consulta del mapa completo se mide por separado de la revelación incremental.
