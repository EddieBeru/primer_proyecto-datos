# Feature Specification: Verificación de resolubilidad

**Feature Branch**: sin rama dedicada; carpeta `003-resolubilidad` (independiente de la rama Git)

**Created**: 2026-11-05

**Status**: Draft — aclaraciones de esta sesión resueltas; lista para planificación.

**Input**: descripción del usuario y bloque 003 de la guía de parte II.

## Clarifications

### Session 2026-11-16
- Q: ¿Una misma llave puede abrir varias puertas y cuántas llaves requiere cada puerta? → A: Según P1 §2.4 y §2.5, una llave abre las puertas cuya llave requerida coincide con su id y no se consume; puede abrir varias puertas. P1 §2.1 y §3, en el esqueleto, describen una única llave por salida cerrada, no combinaciones de llaves.
- Q: ¿Dónde se declaran `llave_salida` y `sala_salida` según P1? → A: En los datos generales de cada cripta, junto con `sala_inicial` (P1 §2.1 y §3, «Datos generales de una cripta»); no se deducen de nombres, ubicaciones ni números fijos. El ejemplo de P1 declara `sala_salida: 19` y `llave_salida: "itm_llave_negra"`, como valores ilustrativos.
- Q: ¿Cómo se trata una puerta cerrada sin llave declarada o cuya llave no aparece en la consulta de ubicaciones? → A: Decisión del usuario, opción A: sin llave declarada se informa un error de datos y no se emite veredicto; si la llave declarada falta en una consulta completa, la puerta se considera bloqueada y la llave no obtenible, con ubicación no declarada.
- Q: ¿Qué criterio concreto determina el orden cuando hay varios válidos? → A: El usuario acepta la recomendación A: orden de descubrimiento, atendiendo salas en el orden en que se descubren, salidas N, S, E, O y llaves de cada sala en el orden de la consulta de ubicaciones. Las dependencias de acceso prevalecen; no se exige el menor id.
- Q: Si existen varios ciclos bloqueantes, ¿cuántos se reportan y cómo se elige? → A: El usuario autoriza aplicar las recomendaciones restantes: se reporta un solo ciclo concreto: se elige la primera llave inaccesible, en el orden de la consulta, que participe en uno; desde ella se toma el primer retorno siguiendo dependencias en el orden del esqueleto, con direcciones N, S, E, O. Se sigue cada dependencia hasta cerrarla o agotarla antes de pasar a la siguiente; cada relación identifica la puerta y la ubicación que la justifican. No se enumeran todos los ciclos.
- Q: ¿Qué formato de texto se usa en `--verificar` y en la interfaz? → A: El usuario autoriza aplicar las recomendaciones restantes: ambos muestran el mismo contenido textual en español y con identificadores explícitos, con resultado y orden de llaves si es resoluble; o motivo, llaves no obtenibles, frontera, ubicaciones y un ciclo si no lo es. Las categorías vacías se indican expresamente; la interfaz puede envolver líneas y permitir desplazamiento sin cambiar contenido ni orden.

- Q: ¿Puede mostrarse un ciclo de alternativas bloqueadas si ninguna llave del paso es imprescindible por todas las rutas? → A: Sí; el usuario acepta la recomendación con «pues hazlo». Se muestra un ciclo concreto y se explican las demás alternativas aún bloqueadas. Cada flecha corresponde a una alternativa de acceso, no a un requisito individual inevitable por todas las rutas.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verificación de resolubilidad (Priority: P1)

Como jugador, quiero saber antes de jugar si puedo ganar y conocer las causas cuando no sea posible.

**Why this priority**: es el comportamiento central de esta capacidad y permite verificar su valor de forma aislada con una partida preparada.

**Independent Test**: ejecutar los escenarios siguientes en una cripta preparada y comparar el resultado observable con el esperado, sin depender de otras capacidades salvo las dependencias indicadas.

**Acceptance Scenarios**:

Los casos siguientes conservan los escenarios atribuidos al Apéndice B por la guía; cada uno especifica condición, acción y resultado esperado.

1. `llave_salida` está detrás de la única puerta que ella misma abre: no resoluble; el reporte señala el ciclo.
2. Una llave está en el campo `suelta` de un enemigo errante: la verificación la ubica en la sala inicial del enemigo.
3. Existen varios órdenes válidos de obtención: dos ejecuciones producen el mismo orden.
4. Cripta no resoluble sin `--forzar`: la partida no inicia y se muestra el reporte.
5. Dos puertas requieren la misma llave accesible: ambas pueden abrirse con ella, sin consumirla ni exigir una copia adicional.
6. Los datos generales declaran una salida y llave distintas de las del ejemplo de P1: el veredicto usa los valores declarados, sin asumir sala 19 ni `itm_llave_negra`.
7. Una puerta cerrada no declara llave: se identifica la puerta en un error de datos y no se declara la cripta resoluble ni no resoluble.
8. Una puerta cerrada requiere una llave ausente de la consulta completa: se continúa la verificación con esa puerta bloqueada; si la cripta es no resoluble, el reporte incluye la llave como no obtenible y su ubicación como no declarada. Una ruta alternativa de victoria puede permitir un resultado resoluble.

9. Desde el inicio son alcanzables dos salas por N y E, con llaves Z y A respectivamente y sin llaves en el inicio: el orden es Z, A por descubrimiento N antes de E, aunque A sea menor por id. Si una sala contiene varias llaves, se conserva el orden relativo de la consulta.
10. Dos ciclos bloqueantes independientes están presentes: el reporte muestra solo el primero según FR-RES-07, con la misma secuencia y justificación en dos ejecuciones idénticas; no omite por ello otras llaves no obtenibles ni puertas de frontera.
11. La misma cripta se verifica con `--verificar` y al intentar iniciar desde la interfaz: ambos reportes conservan resultado, secciones, entradas y orden de FR-RES-15; el ajuste de líneas no elimina texto. Una categoría sin elementos se identifica expresamente.
12. Una cripta no resoluble no tiene ciclos ni puertas de frontera: el reporte explica la condición de victoria incumplida, indica `ninguna` en la frontera y `ninguno` en el ciclo.

13. A se obtiene mediante una puerta B o una puerta C, mientras B y C están detrás de puertas A y no hay otras entradas: se informa no resoluble y un ciclo concreto como `A -> B -> A`, explicando también que la alternativa por C sigue bloqueada. No se afirma que B sea imprescindible para A. Si C pasa a estar accesible, desaparece ese bloqueo circular.

### Edge Cases

- Una llave detrás de su propia puerta exige informar el ciclo concreto.
- La llave que suelta un errante se ubica donde inicia, no donde podría moverse.
- Puede haber rutas alternativas que eviten una aparente dependencia: no deben reportarse como bloqueo inevitable.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-RES-01**: antes de iniciar una partida se determina si la cripta es resoluble, usando el esqueleto y la ubicación de las llaves.
- **FR-RES-02**: supuestos: se atraviesan salidas abiertas y cerradas con llave obtenida; las llaves no se consumen; todo enemigo es derrotable; la llave de un enemigo se obtiene en la sala donde inicia; trampas y cierres automáticos no bloquean.
- **FR-RES-03**: resoluble = desde la sala inicial se puede obtener `llave_salida` y llegar a `sala_salida` por una puerta que la requiere. `sala_inicial`, `sala_salida` y `llave_salida` se toman de los datos generales de la cripta (P1 §2.1 y §3); no se infieren ni se fijan a los valores del ejemplo.
- **FR-RES-04**: si es resoluble, se entrega un orden de obtención donde cada llave va después de todas las necesarias para alcanzarla.
- **FR-RES-05**: el orden es determinista para los mismos datos de entrada: se atienden las salas pendientes en orden de descubrimiento, empezando por `sala_inicial`; en cada sala se registran primero las llaves en el orden de la consulta de ubicaciones y se examinan después las salidas N, S, E, O. Cada sala se descubre una sola vez, cuando su acceso es posible. Cuando una llave habilita varias puertas pendientes, estas se consideran en el orden en que se identificaron por primera vez. Una llave aparece una sola vez y después de las necesarias para alcanzarla; no se exige orden por id. El orden de páginas, salas y ubicaciones forma parte de la entrada; no se promete invariancia ante entradas reordenadas.
- **FR-RES-06**: si no es resoluble, el reporte lista las llaves no obtenibles, las puertas de la frontera bloqueada con su llave requerida, y la ubicación de cada una de esas llaves.
- **FR-RES-07**: si hay ciclos de dependencias entre alternativas de acceso que permanecen bloqueadas, directos o por cadena, el reporte señala exactamente uno: se elige la primera llave inaccesible, en el orden de la consulta de ubicaciones, que participe en un ciclo; desde ella se elige el primer retorno según el orden de dependencias definido a continuación. Las dependencias de cada llave se consideran según el orden de salas del esqueleto (páginas en orden declarado) y direcciones N, S, E, O; se sigue cada dependencia hasta cerrar el retorno a la llave elegida o agotarla antes de pasar a la siguiente, sin volver a examinar dependencias ya agotadas. El ciclo se presenta desde la llave elegida y termina repitiendo esa misma llave; cada paso identifica puerta, llave requerida y ubicación que justifican el bloqueo. Cada paso describe una alternativa bloqueada, no una llave imprescindible por todas las rutas. El reporte acompaña el ciclo con las demás alternativas de acceso y el requisito no satisfecho que bloquea cada una; una alternativa accesible invalida el bloqueo de la llave y no puede presentarse como parte de ese ciclo. Los ciclos de salas sin dependencia de llaves no se reportan como ciclos de llaves. La selección usa la información del mismo recorrido, sin recorridos adicionales por llave, y no enumera todos los ciclos.
- **FR-RES-08**: sin `--forzar`, una cripta no resoluble no inicia partida y se muestra el reporte; con `--forzar`, inicia.
- **FR-RES-09**: `--verificar <cripta>` ejecuta solo la verificación, sin instanciar la vista.
- **FR-RES-10**: la interfaz muestra el reporte de resolubilidad al intentar iniciar una partida, incluso si se bloquea el inicio, con el mismo contenido textual y orden de secciones que `--verificar`. El formato se define en FR-RES-15; puede ajustar líneas y permitir desplazamiento para conservar el acceso a todo el texto.
- **FR-RES-11**: las llaves se obtienen de la consulta de ubicación de llaves, que cuenta dentro de `presupuesto_solicitudes` y se puede persistir con la versión de la cripta.
- **FR-RES-12** (rendimiento): ≤ 200 ms en la cripta publicada más grande; costo ≈ lineal en salas, salidas y llaves; reporte y orden salen del mismo recorrido.
- **FR-RES-13** (medición): `--bench` compara el recorrido único con el recorrido repetido por llave, con criptas sintéticas de muchas llaves encadenadas, deterministas por semilla.
- **FR-RES-14**: una puerta cerrada sin llave declarada impide emitir un veredicto de resolubilidad: se informa un error de datos identificando la puerta. Si declara una llave ausente de la consulta completa de ubicaciones, la verificación continúa considerando esa puerta bloqueada y la llave no obtenible, con ubicación no declarada. Una consulta incompleta o fallida no demuestra que la llave no exista.

- **FR-RES-15**: el reporte usa texto en español con identificadores completos. Comienza con `Cripta: <id>` y `Resultado: RESOLUBLE`, `Resultado: NO RESOLUBLE` o `Resultado: VERIFICACIÓN INCOMPLETA`. Si es resoluble, sigue `Orden de llaves:` y una entrada numerada por llave con id y ubicación. Si no lo es, sigue `Motivo:` indicando las condiciones de victoria incumplidas y luego, en este orden, `Llaves no obtenibles:`, `Frontera bloqueada:`, `Ubicaciones:` y `Ciclo bloqueante:`. Las llaves se listan en el orden de la consulta; las requeridas sin ubicación se añaden por primera aparición en el esqueleto. Las puertas de frontera se listan según salas del esqueleto y direcciones N, S, E, O. Cada puerta se identifica como `sala <origen> / <dirección> -> sala <destino>; requiere <llave>`. Cada ubicación indica `sala <id>` y, si corresponde, `enemigo <id> (sala inicial)`; una ubicación ausente dice `ubicación no declarada`. Las listas vacías dicen `ninguna` y la ausencia de ciclo dice `ninguno`. Un ciclo se escribe `A -> B -> A`, donde `A -> B` significa que una alternativa bloqueada para obtener A requiere B, seguido de las puertas y ubicaciones que justifican cada paso y de las otras alternativas aún bloqueadas con su causa. No significa que B sea imprescindible por todas las rutas. Con información incompleta, se muestra `Motivo:` y el error concreto, sin afirmar imposibilidad ni inventar un orden o un ciclo.

### Key Entities

- Resultado: resoluble con orden de llaves, o no resoluble con diagnóstico.
- Llave: identificador y ubicación, incluido el inicio de un enemigo que la suelta.
- Frontera bloqueada: puertas cerradas adyacentes a salas alcanzables y sus llaves.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-RES-01**: Verificación y diagnóstico en como máximo 200 ms en la cripta publicada más grande.
- **SC-RES-02**: El trabajo total crece aproximadamente de forma lineal con salas, salidas y llaves, sin un recorrido completo por llave.
- **SC-RES-03**: Dos ejecuciones con la misma entrada producen el mismo orden o diagnóstico conforme a FR-RES-05 y FR-RES-07; una cripta no resoluble no inicia sin `--forzar`.
- **SC-RES-04**: Todos los escenarios de puertas sin llave declarada y llaves ausentes de la consulta completa distinguen error sin veredicto de bloqueo comprobado, conforme a FR-RES-14.
- **SC-RES-05**: En todos los casos de prueba, consola e interfaz conservan el contenido y orden del reporte de FR-RES-15, incluidos identificadores, categorías vacías y justificación del ciclo elegido.

## Assumptions

- Fuentes: [guía de parte II](../../docs/CRIPTA%20Parte%20II%20gu%C3%ADa%20y%20divisi%C3%B3n%20del%20trabajo.md), [P1](../../docs/enunciado.md) y [constitución](../../.specify/memory/constitution.md).
- La guía es un resumen y una propuesta de trabajo, no el enunciado íntegro de P2. Sus referencias deben contrastarse con ese enunciado cuando esté disponible.
- Los requisitos copiados de la guía son la base solicitada; los supuestos siguientes son propuestas explícitas para revisión, no nuevas reglas oficiales.
- El desempate aprobado es el orden de descubrimiento definido en FR-RES-05; no se exige orden por id ni invariancia ante un reordenamiento de la entrada.
- Si existen varios ciclos bloqueantes, se informa exactamente uno conforme a FR-RES-07. Esta elección y el desempate son decisiones aprobadas por el usuario, no reglas atribuidas a P1.
- Conforme a P1 §2.4 y §2.5, una misma llave puede abrir varias puertas cuya llave requerida coincide con su id y no se consume. Cada salida cerrada declara una sola llave requerida (P1 §2.1 y §3); no se contemplan combinaciones de llaves.
- La ausencia de una llave en la consulta completa de ubicaciones se trata como llave no obtenible, con ubicación no declarada; no se inventa una ubicación. La ausencia de llave declarada en una puerta cerrada es un error de datos que impide emitir veredicto, conforme a FR-RES-14.
- El reporte comparte contenido y formato textual entre consola e interfaz según FR-RES-15; el diseño visual concreto queda para planificación, respetando las reglas de interfaz del proyecto.
- El límite de cálculo se mide con esqueleto y ubicaciones disponibles, separando el tiempo variable de red.
- Los límites temporales son criterios de aceptación pendientes de medición; este documento no afirma que ya se cumplan. La máquina y carga reproducible se precisarán al planificar.

### Descripción de entrada conservada

Capacidad: verificación de resolubilidad. Antes de iniciar una partida, el programa determina si la cripta puede ganarse y, si no, explica por qué.

Se usa el esqueleto y la ubicación de las llaves. Supuestos: el jugador puede atravesar cualquier salida abierta y cualquier salida cerrada cuya llave ya obtuvo; las llaves no se consumen; todo enemigo puede ser derrotado; una llave que suelta un enemigo se considera obtenible en la sala donde ese enemigo inicia; las trampas y los cierres automáticos no bloquean, porque una puerta puede volver a abrirse con la misma llave.

Una cripta es resoluble si, partiendo de la sala inicial y bajo esos supuestos, el jugador puede obtener llave_salida y llegar a sala_salida a través de una puerta que la requiere.

Si es resoluble, el resultado es un orden de obtención de llaves en el que cada llave aparece después de todas las llaves necesarias para alcanzarla. Si hay varios órdenes válidos, cualquiera sirve, pero el resultado es determinista (dos ejecuciones dan el mismo orden).

Si no es resoluble, el resultado informa: las llaves que no pueden obtenerse; las puertas de la frontera bloqueada (puertas cerradas adyacentes a la región alcanzable) con la llave que requiere cada una; y dónde se encuentra cada una de esas llaves. Si una llave está detrás de puertas que solo ella abre, directamente o por una cadena de llaves, el reporte señala el ciclo concreto, de forma determinista.

Si la cripta no es resoluble, la partida no inicia salvo que se use --forzar, y se muestra el reporte. La bandera --verificar <cripta> ejecuta solo la verificación, sin instanciar la vista. La interfaz muestra el reporte al iniciar una partida.

Rendimiento: ≤ 200 ms en la cripta publicada más grande. El costo total crece aproximadamente de forma lineal con salas, salidas y llaves; no se repite un recorrido completo por cada llave obtenida, y el reporte sale del mismo recorrido, sin recorridos adicionales por llave. Las llaves se obtienen de la consulta de ubicación de llaves del servicio, que cuenta dentro de presupuesto_solicitudes.
