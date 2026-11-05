# Feature Specification: Verificación de resolubilidad

**Feature Branch**: sin rama dedicada; carpeta `003-resolubilidad` (independiente de la rama Git)

**Created**: 2026-11-05

**Status**: Draft — pendiente de revisión con `$speckit-clarify`

**Input**: descripción del usuario y bloque 003 de la guía de parte II.

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

### Edge Cases

- Una llave detrás de su propia puerta exige informar el ciclo concreto.
- La llave que suelta un errante se ubica donde inicia, no donde podría moverse.
- Puede haber rutas alternativas que eviten una aparente dependencia: no deben reportarse como bloqueo inevitable.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-RES-01**: antes de iniciar una partida se determina si la cripta es resoluble, usando el esqueleto y la ubicación de las llaves.
- **FR-RES-02**: supuestos: se atraviesan salidas abiertas y cerradas con llave obtenida; las llaves no se consumen; todo enemigo es derrotable; la llave de un enemigo se obtiene en la sala donde inicia; trampas y cierres automáticos no bloquean.
- **FR-RES-03**: resoluble = desde la sala inicial se puede obtener `llave_salida` y llegar a `sala_salida` por una puerta que la requiere.
- **FR-RES-04**: si es resoluble, se entrega un orden de obtención donde cada llave va después de todas las necesarias para alcanzarla.
- **FR-RES-05**: el orden es determinista: dos ejecuciones sobre la misma cripta dan el mismo orden.
- **FR-RES-06**: si no es resoluble, el reporte lista las llaves no obtenibles, las puertas de la frontera bloqueada con su llave requerida, y la ubicación de cada una de esas llaves.
- **FR-RES-07**: si hay un ciclo de dependencia (directo o por cadena), el reporte señala el ciclo concreto, de forma determinista.
- **FR-RES-08**: sin `--forzar`, una cripta no resoluble no inicia partida y se muestra el reporte; con `--forzar`, inicia.
- **FR-RES-09**: `--verificar <cripta>` ejecuta solo la verificación, sin instanciar la vista.
- **FR-RES-10**: la interfaz muestra el reporte de resolubilidad al iniciar una partida.
- **FR-RES-11**: las llaves se obtienen de la consulta de ubicación de llaves, que cuenta dentro de `presupuesto_solicitudes` y se puede persistir con la versión de la cripta.
- **FR-RES-12** (rendimiento): ≤ 200 ms en la cripta publicada más grande; costo ≈ lineal en salas, salidas y llaves; reporte y orden salen del mismo recorrido.
- **FR-RES-13** (medición): `--bench` compara el recorrido único con el recorrido repetido por llave, con criptas sintéticas de muchas llaves encadenadas, deterministas por semilla.

### Key Entities

- Resultado: resoluble con orden de llaves, o no resoluble con diagnóstico.
- Llave: identificador y ubicación, incluido el inicio de un enemigo que la suelta.
- Frontera bloqueada: puertas cerradas adyacentes a salas alcanzables y sus llaves.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-RES-01**: Verificación y diagnóstico en como máximo 200 ms en la cripta publicada más grande.
- **SC-RES-02**: El trabajo total crece aproximadamente de forma lineal con salas, salidas y llaves, sin un recorrido completo por llave.
- **SC-RES-03**: Dos ejecuciones con la misma entrada producen el mismo orden o diagnóstico; una cripta no resoluble no inicia sin --forzar.

## Assumptions

- Fuentes: [guía de parte II](../../docs/CRIPTA%20Parte%20II%20gu%C3%ADa%20y%20divisi%C3%B3n%20del%20trabajo.md), [P1](../../docs/enunciado.md) y [constitución](../../.specify/memory/constitution.md).
- La guía es un resumen y una propuesta de trabajo, no el enunciado íntegro de P2. Sus referencias deben contrastarse con ese enunciado cuando esté disponible.
- Los requisitos copiados de la guía son la base solicitada; los supuestos siguientes son propuestas explícitas para revisión, no nuevas reglas oficiales.
- Ante varios órdenes válidos basta un criterio estable reproducible; no se exige orden por id.
- Si existen varios ciclos bloqueantes, se informa al menos uno concreto de forma determinista.
- Una llave puede abrir varias puertas; una puerta requiere la llave declarada por el servicio.
- Una llave requerida sin ubicación se informa como no obtenible y ubicación no declarada; no se inventa una ubicación.
- Una puerta cerrada sin llave utilizable no es atravesable bajo los supuestos dados.
- El reporte presenta la misma información en consola e interfaz sin imponer diseño visual.
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
