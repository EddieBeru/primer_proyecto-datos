# Implementation Plan: Verificación de resolubilidad

**Branch**: función `003-resolubilidad`; rama Git real `main`, sin crear rama dedicada | **Date**: 2026-11-16 | **Spec**: [spec.md](spec.md)

**Input**: especificación003 aclarada, restricciones obligatorias del usuario y autorización «pues hazlo» para ciclos de alternativas bloqueadas. El nombre `BRANCH` informado por setup identifica la función; `git branch --show-current` informa `main`.

## Summary

Comprobar antes de jugar si se obtiene `llave_salida` y existe entrada a `sala_salida` por una puerta que la requiere; devolver orden determinista o diagnóstico con llaves inaccesibles, frontera final y un ciclo concreto acompañado de sus alternativas bloqueadas. Compilar una vez el esqueleto común001/003 y resolverlo mediante propagación incremental de hechos con suscriptores; obtener reporte y orden de las mismas evidencias, sin búsquedas por llave. Proponer `/criptas/{id}/llaves`, su presupuesto/persistencia versionada, las banderas y el reporte común para consola/vista.

Fases0 y1 completas en diseño: [research](research.md), [modelo](data-model.md), [contratos](contracts/interfaces.md), [esqueleto común](contracts/esqueleto-compartido.md) y [guía de validación](quickstart.md). No se crean tareas ni implementación del verificador. Las mediciones preliminares reales se limitan a estructuras, con script y muestras versionables.

## Technical Context

**Language/Version**: Python≥3.11; entorno medido3.12.3.

**Primary Dependencies**: dependencias actuales requests/pygame-ce; sin nuevas bibliotecas de grafos. pytest para aceptación.

**Storage**: respuesta `/llaves` opcional en disco con id/versión de cripta y formato1; no cambiar guardado v4 ni bitácora.

**Testing**: pytest offline con falsos, oráculo lento acotado, instrumentación de visitas, subprocess CLI sin vista y SDL dummy para integración gráfica. En esta fase solo comprobaciones documentales y microbenchmarks de estructuras.

**Target Platform**: Linux escritorio, consola y Pygame; algoritmo independiente de red/vista.

**Project Type**: juego existente, manteniendo C1→datos, C2→reglas, orquestador→coordinación y vista→Sesión/DTO.

**Performance Goals**: ≤200 ms de trabajo local completo sobre mayor cripta publicada. Tiempo/espacio esperado O(S+E+K+L+B+R), B bytes totales de identificadores y R texto emitido; para ids acotados, ubicaciones O(K) y reporte compartido de tamaño lineal: aproximadamente O(S+E+K). Índice propio esperado amortizado, sin garantía adversaria de hash. IDs numéricos de tamaño de máquina; si se admiten enteros arbitrariamente largos, contabilizar también el costo real de sus operaciones. Hash textual propio lineal en bytes, sin convertir IDs textuales en enteros grandes.

**Constraints**: prohibidos `heapq`, `deque`, `set` y sus auxiliares en003; tampoco `frozenset` como sustituto. No dict como índice, `sorted`, `list.sort`, `pop(0)`, recursión dependiente de cantidad de llaves, búsqueda completa por llave ni producto cartesiano entre llaves. JSON permitido solo para transporte/informe. No leer otra vez todo el esqueleto para generar reporte.

**Scale/Scope**: S salas, E salidas declaradas, K ids de llave, L ubicaciones; E≤4S, incluyendo sentidos declarados. Tamaño/version de mayor cripta publicada no disponible localmente: objetivo de aceptación pendiente, no reemplazar por sintéticas.

## Constitution Check

Gates revisados antes de investigación y después del diseño.

| Principio | Revisión inicial | Revisión posterior |
|---|---|---|
| I. Enunciado | P1 y guía local leídos; alcance003 dado por usuario. | Conflicto de dependencias inevitables resuelto por autorización explícita y ajuste FR-RES-07/15; no se inventa enunciado P2. |
| II. Fronteras/contratos | K1/K5 y enmiendas existentes revisados. | Cambios propuestos y reviewables en contracts/, sin editar acuerdos firmados; aceptación regla6.3 previa a implementar. |
| III. Estructuras/mediciones | No usar auxiliares prohibidos ni duplicar esqueleto001. | Estructuras propias, evidencia parcial reproducible en DECISIONES.md; meta completa pendiente. |
| IV. Determinismo/compatibilidad | Conservar reloj/RNG/replay/guardado. | Criterios explícitos; nueva partida separada de carga/replay; caché versionada independiente de v4. |
| V. Validación | Pruebas offline y presupuesto necesarias. | Guía incluye oráculo, alternativas, instrumentación, CLI/UI y medición; no se declara ejecución de pruebas futuras. |
| VI. Spec Kit | Función003 seleccionada por usuario. | Plan e investigación/modelo/contratos/quickstart; sin tasks ni implementación anticipadas. |
| VII. Trazabilidad LLM | Registrar prompt/uso/limitaciones. | PROMPTS_LLM.md y DECISIONES.md actualizados; sin credenciales ni atribución de aprobaciones ajenas. |

**Resultado:** diseño sin excepciones constitucionales. Las propuestas de contrato y la disponibilidad de servicio/cripta son dependencias de integración/aceptación, no aprobaciones implícitas. No existen hooks en `.specify/extensions.yml`.

## Project Structure

### Documentation (this feature)

```text
specs/003-resolubilidad/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── interfaces.md
    └── esqueleto-compartido.md
docs/mediciones/
├── 003-estructuras-plan.py
└── 003-estructuras-plan.json
DECISIONES.md
PROMPTS_LLM.md
```

### Source Code (repository root)

Rutas existentes a ampliar y nuevas propuestas para la implementación posterior:

```text
src/models/rooms.py                    # Exit con costo, compartido001
src/models/conocimiento.py             # DatosSalida y constructor compartido001/002/003
src/models/resolubilidad.py            # DTO ubicaciones/resultado/evidencias
src/estructuras/tabla_indice.py         # índice propio reutilizado
src/estructuras/cola_fifo.py            # cola propia con arreglo+cursor
src/algoritmos/resolubilidad.py         # propagación y reducción residual pura
src/controller1/endpoints.py           # /criptas/{id}/llaves con budget
src/controller1/offline.py             # ubicaciones offline
src/controller1/almacen_llaves.py       # persistencia versionada de insumo
src/controller1/cli.py                 # configuración de banderas
src/orchestrator/sesion.py             # preparación, confirmación y DTO
src/orchestrator/reporte_resolubilidad.py # formateo común
src/orchestrator/bench_resolubilidad.py # sintéticas y referencia repetida
src/orchestrator/bench.py              # registro en --bench
src/main.py                           # despacho sin vista antes de importarla
src/view/app.py                        # presentación del reporte vía Sesión
src/view/pantallas.py                  # panel con texto completo/scroll
tests/test_resolubilidad.py
tests/test_llaves.py
tests/test_bench_resolubilidad.py
tests/test_cli_resolubilidad.py
tests/test_vista_resolubilidad.py
```

**Structure Decision**: no importar C1 desde C2/algoritmo ni duplicar tipos del esqueleto. Modelo neutral y estructuras propias accesibles a001/003; Sesión coordina y la vista solo presenta.

## Decisiones de implementación y trazabilidad

| Decisión | FR cubiertos | Artefacto/evidencia |
|---|---|---|
| D01: esqueleto compartido con costo/llave/puerta inicial | FR-RES-01,02,03,11,12 | contrato común, modelos actuales e integración001 |
| D02: hechos monotónicos, reglas de acceso y suscriptores | FR-RES-01,02,03,04,05,06,12 | invariantes y contadores abajo |
| D03: FIFO propia, índices/ordinales y marcas; sin prohibidos | FR-RES-05,07,12,13 | microbenchmarks reales y DECISIONES.md |
| D04: orden fuente y descubrimiento reproducible | FR-RES-04,05,07,15 | reglas de desempate y pruebas de orden |
| D05: ciclo residual con alternativas, no dependencias inevitables | FR-RES-06,07,12,15 | aclaración aprobada, escenario13 y reducción lineal |
| D06: /llaves, budget único y caché por versión | FR-RES-01,02,11,14 | interfaces.md y falsos presupuestados |
| D07: preparar/confirmar, CLI sin vista, reporte común | FR-RES-08,09,10,14,15 | contratos de ciclo de vida y UI |
| D08: oráculo, visitas y medición completa | FR-RES-01–15 | quickstart y --bench |

### Recorrido incremental único — D01/D02/D04 (FR-RES-01–06/12)

1. C1 entrega datos generales, páginas ordenadas y ubicaciones completas de igual versión. Ingestión común única produce ordinales, adjacencias y reglas/inversas en O(S+E+L); cada registro de salida del transporte se lee una vez. Validar todas las puertas, incluso las de salas no alcanzables, para no ocultar una puerta sin llave declarada.
2. Activar `sala_inicial`, marcar al descubrir y agregar a FIFO. La marca de descubrimiento no dispara reglas salientes: una compuerta de procesamiento por sala las habilita únicamente cuando se atiende esa sala, después de sus llaves. La compilación no establece el orden de pendientes: se enlazan al identificar cada puerta durante la exploración. Al atender una sala, obtener primero sus llaves por orden de consulta y despertar exclusivamente los suscriptores de cada llave nueva; considerar después sus salidas N,S,E,O. Una puerta cerrada se registra pendiente con ordinal de primera identificación si falta su llave. Si una misma llave desbloquea varias, procesarlas en ese ordinal. Una sala ya descubierta no vuelve a la FIFO.
3. Los contadores/suscriptores aseguran que cada premisa se satisface una sola vez y cada regla dispara como máximo una. Una puerta cerrada requiere origen y llave; recibir la llave antes de llegar al origen también debe funcionar. No examinar pendientes de otras llaves al obtener una. No barrer de nuevo las salidas de salas procesadas.
4. Mantener testigo de primera entrada, orden de llaves y evidencia por salida/regla. Seguir hasta agotar la FIFO aun si ya existe victoria, para incluir todas las llaves obtenibles. La comprobación de victoria exige llave final obtenida y una salida hacia la sala final que la requiere y puede cruzarse desde región alcanzable; no basta entrada libre por otra puerta.
5. Congelar marcas. Enumerar secuencias de llaves y evidencias pendientes una vez para obtener no obtenibles y frontera final. Esta enumeración no vuelve al proveedor/esqueleto ni calcula rutas por llave. Puertas con ambos extremos alcanzables o llave obtenida no son frontera. Llaves opcionales inaccesibles no invalidan una victoria.

**Invariantes:** activaciones≤S+K; reglas de salidas≤E; reglas de ubicación≤L; notificaciones≤2E+L; primera inspección de salida≤E; reactivación por llave≤E. Estructuras y reporte O(S+E+K+L). Constructor y reducción global suman constantes, no un factorK.

### Ciclo concreto y desempate — D04/D05 (FR-RES-05/06/07/12/15)

Las alternativas se conservan como reglas AND/OR, con referencias a salas/puertas/ubicaciones; no crear el grafo cuadrático «todas las llaves necesarias para cada llave». Tras agotar activaciones, filtrar las evidencias falsas ya compiladas. Una consecuencia falsa apunta a todas sus reglas alternativas, y una regla pendiente apunta a sus premisas aún falsas. Se conserva por qué cada acceso permanece bloqueado.

Tarjan iterativo propio visita esa evidencia globalmente en O(nodos+incidencias), con arreglos de índice/lowlink/en_pila y pila de marcos. Cada nodo e incidencia entra una vez. No usa recursión, heap ni set. Recorrer después componentes/incidencias una vez para identificar las que contienen un circuito con llave y una dependencia de puerta cerrada; los ciclos de salas abiertas no califican. No reiniciar Tarjan por llave ni recorrer el esqueleto para este paso.

**Selección concreta:** las llaves candidatas se consideran en orden de la consulta. Elegir la primera que pertenezca a un circuito de dependencias residuales con puerta/llave; desde ella buscar un solo primer retorno dentro de su componente, siguiendo dependencias por ordinal de sala fuente y N,S,E,O, y ubicaciones por orden de consulta. Orden fijo de premisas: origen antes de llave cuando ambas falten. La búsqueda usa marcas y pila propias, visita cada incidencia como máximo una vez y se ejecuta una sola vez para el testigo elegido, no una vez por llave. La primera llave elegible se determina por los componentes ya calculados, no probando rutas para cada candidata. La salida repite esa llave al cerrar el circuito.

Colapsar los segmentos de salas/reglas en flechas entre llaves conservando puertas, sentidos y ubicaciones de cada tramo. Compartir referencias para no copiar una ruta larga por cada llave. Adjuntar las otras reglas alternativas pendientes y sus causas; no enumerar todos los caminos ni todos los circuitos. Mostrar un circuito no sustituye la prueba de imposibilidad: esta surge del agotamiento de la propagación y de la condición de victoria incumplida.

**Qué significa un solo recorrido:** existe una única exploración incremental de alcanzabilidad sobre el modelo compilado. La ingestión y la reducción global de evidencias tienen costo lineal y visitas explícitas contabilizadas; no se promete literalmente una sola lectura de cada arreglo auxiliar. El diagnóstico no hace otra búsqueda de alcanzabilidad sobre el esqueleto ni un recorrido adicional por llave. Medir por separado ingestión, propagación, reducción y texto, y sumar todo en el tiempo de aceptación.

### Cambio API y ciclo de inicio — D06/D07 (FR-RES-08–11/14/15)

La propuesta de `/llaves`, formato, cache y presupuesto se encuentra en contracts/interfaces.md. El cliente actual necesita corregir el bootstrap para contar solo listas realmente realizadas y no silenciar falta de presupuesto. Mantener el mismo BudgetAdapter entre preparación y partida. No cargar catálogo/contenidos hasta permitir el inicio. Capturar errores sin instalar estado parcial.

`--verificar` despacha a la preparación y formateador sin importación/instanciación de vista. `--forzar` permite únicamente un negativo comprobado. En interfaz, reporte común con panel legible y scroll, visible antes de continuar o volver; DTO disponible también si no hay FotoEstado nueva. Carga y replay no pasan por la política nueva de inicio para preservar partidas anteriores/forzadas.

Auditar dependencias: hoy hay set heredados en caché/proveedor/vista. La verificación no los instancia ni reutiliza; los auxiliares que003 incorpore a la integración también deben usar estructuras permitidas. La prohibición no se oculta mediante wrappers ni imports de colecciones. Las dependencias de otros subsistemas se registran sin declarar cumplimiento global del repositorio. Regresión de integración tras modificar los puntos compartidos.

## Validation Strategy

| FR | Validación prevista |
|---|---|
| FR-RES-01/02/03 | esqueleto común, salida requerida, llave de errante en inicio, puertas abiertas, no consumo, trampas/cierre ignorados |
| FR-RES-04/05 | todos los obtenibles una vez, dependencia previa, N antes de E aun si id mayor, misma llave en varias ubicaciones,100 repeticiones idénticas |
| FR-RES-06/07 | frontera final exacta, ciclos directo/cadena/alternativas, circuito sin llaves descartado, desconexión sin ciclo, causas compartidas sin explosión |
| FR-RES-08/09/10 | bloqueo antes de estado/log, forzado con reporte, verificar sin vista, reporte idéntico en UI y consola, carga/replay preservados |
| FR-RES-11/14 | HTTP e intentos contados, budget único/agotado, cache vigente/obsoleta/corrupta, offline incompleto, llave ausente frente a puerta sin llave |
| FR-RES-12 | inspecciones/notificaciones acotadas, reducción global lineal, no recorrido por llave, tiempo local completo≤200 ms en mayor publicada |
| FR-RES-13 | sintéticas encadenadas por semilla, comparador de barridos repetidos, datos iguales y contadores/tiempos por tamaño |
| FR-RES-15 | formato textual, IDs íntegros, secciones/valores vacíos, ciclo con sus alternativas, error sin veredicto |

Instrumentar AST e imports de los archivos nuevos para detectar `heapq`, `deque`, `set`, `frozenset`, aliases y comprensiones de conjunto; revisar también las dependencias usadas por el flujo puro/preparador. Dict solo transporte/informe, no marcas ni índices. No imponer esta auditoría como cambio silencioso de todo el juego.

## Plan de medición --bench — D03/D08 (FR-RES-12/13)

Agregar `bench_resolubilidad()` al registro existente: familias con semilla300316, tamaños128,512,2048,8192 llaves, más tamaños escalables si el entorno lo permite. Semilla fija genera IDs dispersos, orden de ubicaciones y ramales deterministas; familias: cadena larga resoluble, cadena circular, muchas puertas para una llave, ramas con alternativas AND/OR y región desconectada. E≤4S. Construir datos idénticos fuera del cronómetro para ambos métodos.

Método incremental de producción frente a referencia de laboratorio que vuelve a recorrer todo el plano con cada llave nueva, recogiéndolas de una en una para exponer el peor caso. La referencia no se importa desde producción, no usa estructuras prohibidas y no autoriza copiarla al verificador. Comparar veredicto, obtenibles y validez del orden; no exigir órdenes idénticos si la referencia usa otro desempate. El oráculo de ciclos se valida en fixtures pequeñas, no inventar equivalencia por un booleano.

Dos calentamientos y al menos7 repeticiones por tamaño/familia; emitir todas las muestras, mediana/máximo, número de visitas y razón de crecimiento por S+E+K+L. Medir perf_counter_ns; separar preparación local, propagación, resumen/ciclo y formato, además de total; registrar memoria aparte para no contaminar tiempo. Anotar intérprete, CPU, SO, commit, semilla, S/E/K/L/B, versión, número de componentes, longitud de reporte y carga del equipo. No usar el mejor tiempo como único dato.

Sobre la mayor cripta publicada, con insumos disponibles/versionados:100 verificaciones, incluir total local y máximo, aceptar solo si todas≤200 ms. Red y renderizado excluidos; no excluir normalización ni diagnóstico para mejorar artificialmente la cifra. Contadores demuestran crecimiento lineal aun si los tiempos pequeños tienen ruido. Si la cripta no está disponible, registrar aceptación pendiente y no reemplazarla por sintética. El `--bench` completo incluye además los subsistemas existentes; distinguir si uno usa auxiliares legados ajenos a003.

## Complexity Tracking

No se solicitan excepciones. Costo esperado O(S+E+K+L+B+R), memoria lineal incluyendo incidencias inversas/evidencia; caso adversario del hash y costo de ids largos declarados. Los pases globales de evidencia residual se cuentan, no se disfrazan como cero trabajo. No hay recorrido completo por llave ni ordenamiento global. La implementación debe comprobar la cota con contadores y pruebas antes de afirmar200 ms o corrección de ciclos.
