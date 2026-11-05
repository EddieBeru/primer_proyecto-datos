# Feature Specification: Línea de tiempo

**Feature Branch**: sin rama dedicada; carpeta `004-linea-de-tiempo` (independiente de la rama Git)

**Created**: 2026-11-05

**Status**: Draft — pendiente de revisión con `$speckit-clarify`

**Input**: descripción del usuario y bloque 004 de la guía de parte II.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Línea de tiempo (Priority: P1)

Como jugador, quiero consultar estados pasados sin alterar la partida ni el retroceso disponible.

**Why this priority**: es el comportamiento central de esta capacidad y permite verificar su valor de forma aislada con una partida preparada.

**Independent Test**: ejecutar los escenarios siguientes en una cripta preparada y comparar el resultado observable con el esperado, sin depender de otras capacidades salvo las dependencias indicadas.

**Acceptance Scenarios**:

Los casos siguientes conservan los escenarios atribuidos al Apéndice B por la guía; cada uno especifica condición, acción y resultado esperado.

1. `historia <t>` con t mayor que el reloj actual: se rechaza.
2. `historia` después de usar un pergamino: no muestra las acciones revertidas.
3. Varios eventos ocurren en el mismo instante t: `historia <t>` muestra el estado después de todos ellos.
4. `historia` no consume tiempo virtual, no se registra en `partida.log` y no modifica el historial de retroceso.
5. `--replay partida.log --hasta t` con t posterior al final: muestra el estado final e indica que la partida terminó antes.
6. Se carga un archivo de partida de la parte 1: se reporta la incompatibilidad o se migra explícitamente; nunca se carga en silencio.

### Edge Cases

- Varios eventos en t se incluyen todos antes de mostrar el estado.
- Consultar el futuro en partida se rechaza; reproducir más allá del final muestra el estado final y lo indica.
- Retroceder elimina de la línea las acciones revertidas.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-LIN-01**: el estado en el instante t es el posterior a todos los eventos con tiempo ≤ t; si a t le corresponde una decisión del jugador, es el estado justo antes de tomarla.
- **FR-LIN-02**: `historia <t>` y `historia #k` (justo antes de la acción k del jugador) están disponibles en partida.
- **FR-LIN-03**: el resumen incluye como mínimo reloj, sala del jugador, vida y estadísticas, inventario, efectos activos, enemigos de esa sala con su vida y el mapa conocido en ese momento.
- **FR-LIN-04**: la consulta no consume tiempo virtual, no se registra como acción en `partida.log` y no altera el estado del juego ni el historial de retroceso.
- **FR-LIN-05**: consultar un instante posterior al reloj actual se rechaza.
- **FR-LIN-06**: `--replay partida.log --hasta <t>` imprime el mismo resumen sin instanciar la vista; si t es posterior al final, muestra el estado final e indica que la partida terminó antes.
- **FR-LIN-07**: las acciones revertidas con un pergamino dejan de existir en la línea.
- **FR-LIN-08**: hay como máximo un punto de control cada K acciones del jugador; K se configura con `--checkpoint-cada` y su valor por defecto se justifica con mediciones.
- **FR-LIN-09**: una consulta aplica o deshace cambios de a lo sumo K acciones del jugador.
- **FR-LIN-10**: fuera de los puntos de control solo se guarda lo necesario para reconstruir cambios; la memoria crece con los cambios más un punto cada K acciones.
- **FR-LIN-11**: el estado reconstruido es idéntico al que tuvo la partida original en ese instante (determinismo).
- **FR-LIN-12**: guardar y cargar conserva la línea completa; un archivo de la parte 1 se reporta como incompatible o se migra explícitamente, nunca en silencio.
- **FR-LIN-13** (rendimiento): `historia` ≤ 50 ms con ≥ 5 000 acciones y K por defecto; usar un pergamino recorta la línea sin recorrer toda la historia.
- **FR-LIN-14** (medición): `--bench` mide memoria y tiempo de consulta con al menos tres valores de K y contra la alternativa sin puntos de control.

### Key Entities

- Instante histórico: estado después de los eventos de tiempo menor o igual a t, antes de una decisión del jugador en ese instante.
- Acción numerada: acción del jugador cuya situación previa puede consultarse.
- Punto de control: estado completo separado según el intervalo K.
- Resumen histórico: reloj, sala, vida, estadísticas, inventario, efectos, enemigos locales y mapa conocido.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-LIN-01**: Consulta historia en como máximo 50 ms con al menos 5 000 acciones y el K por defecto justificado.
- **SC-LIN-02**: Cada consulta aplica o deshace cambios de como máximo K acciones.
- **SC-LIN-03**: Memoria proporcional a los cambios más un punto de control cada K acciones; se comparan al menos tres K y la alternativa sin puntos.
- **SC-LIN-04**: La consulta no altera la partida; retroceder recorta la línea sin recorrer toda la historia; guardar y cargar conserva la línea completa.

## Assumptions

- Fuentes: [guía de parte II](../../docs/CRIPTA%20Parte%20II%20gu%C3%ADa%20y%20divisi%C3%B3n%20del%20trabajo.md), [P1](../../docs/enunciado.md) y [constitución](../../.specify/memory/constitution.md).
- La guía es un resumen y una propuesta de trabajo, no el enunciado íntegro de P2. Sus referencias deben contrastarse con ese enunciado cuando esté disponible.
- Los requisitos copiados de la guía son la base solicitada; los supuestos siguientes son propuestas explícitas para revisión, no nuevas reglas oficiales.
- Cada paso de ir a cuenta como una acción para K y para historia #k.
- Las acciones se numeran desde 1; #0, índices inexistentes y tiempos negativos o no enteros se rechazan sin efectos.
- K debe ser entero mayor o igual que 1; su valor por defecto se decide en el plan con mediciones de al menos tres valores.
- El estado inicial puede conservarse como origen de reconstrucción; no autoriza copias completas por acción.
- Depende del conocimiento definido en 002; se conserva el límite de cinco acciones del pergamino de P1.
- La representación concreta del resumen y la compatibilidad del archivo se fijan al planificar, preservando los comportamientos exigidos.
- Los límites temporales son criterios de aceptación pendientes de medición; este documento no afirma que ya se cumplan. La máquina y carga reproducible se precisarán al planificar.

### Descripción de entrada conservada

Capacidad: línea de tiempo. El pergamino de retroceso (P1 §2.11) sigue limitado a 5 acciones. La línea de tiempo es independiente: permite consultar, sin modificar la partida, el estado en cualquier instante desde el inicio.

Estado en el instante t: el estado después de ejecutar todos los eventos con tiempo menor o igual que t. Si a t le corresponde una decisión del jugador, es el estado justo antes de tomarla.

Consulta en partida: el comando «historia <t>» o «historia #k» (estado justo antes de la acción número k del jugador) muestra como mínimo: reloj, sala del jugador, vida y estadísticas, inventario, efectos activos, enemigos de esa sala con su vida, y el mapa conocido en ese momento. La consulta no consume tiempo virtual, no se registra como acción y no altera ningún estado del juego ni del historial de retroceso. Consultar un instante posterior al reloj actual se rechaza.

Consulta sin interacción: --replay partida.log --hasta <t> reproduce la partida hasta t e imprime el mismo resumen sin instanciar la vista. Si t es posterior al final de la partida, muestra el estado final e indica que la partida terminó antes.

Interacción con el retroceso: las acciones revertidas con un pergamino dejan de existir en la línea; la línea describe la historia tal como quedó.

Restricción de memoria: se permiten copias completas del estado (puntos de control), pero no más de una cada K acciones del jugador. K se configura con --checkpoint-cada K; el valor por defecto lo escoge el grupo y lo justifica con mediciones. Una consulta no puede requerir aplicar o deshacer cambios de más de K acciones del jugador. Fuera de los puntos de control solo se almacena la información necesaria para reconstruir los cambios. La memoria total crece con la cantidad de cambios ocurridos más un punto de control cada K acciones, nunca con acciones por tamaño del estado.

Persistencia: guardar y cargar conserva la línea completa. Un archivo de partida de la primera parte se detecta como incompatible o se migra de forma explícita; nunca se carga en silencio.

Rendimiento: «historia» ≤ 50 ms en una partida de al menos 5 000 acciones con K por defecto. Debe medirse memoria y tiempo de consulta con al menos tres valores de K y contra la alternativa sin puntos de control.
