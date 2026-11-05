# Feature Specification: Terreno y cazador

**Feature Branch**: sin rama dedicada; carpeta `001-terreno-cazador` (independiente de la rama Git)

**Created**: 2026-11-05

**Status**: Draft — pendiente de revisión con `$speckit-clarify`

**Input**: descripción del usuario y bloque 001 de la guía de parte II.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Terreno y cazador (Priority: P1)

Como jugador, quiero que el terreno afecte los tiempos y que el cazador persiga por la ruta más barata.

**Why this priority**: es el comportamiento central de esta capacidad y permite verificar su valor de forma aislada con una partida preparada.

**Independent Test**: ejecutar los escenarios siguientes en una cripta preparada y comparar el resultado observable con el esperado, sin depender de otras capacidades salvo las dependencias indicadas.

**Acceptance Scenarios**:

Los casos siguientes conservan los escenarios atribuidos al Apéndice B por la guía; cada uno especifica condición, acción y resultado esperado.

1. Un cazador sin ruta abierta hacia el jugador espera con costo 100.
2. La ruta más barata cuesta más que su rango: espera con costo 100.
3. Ruta de menos salas pero mayor costo frente a ruta de más salas y menor costo: sigue la de menor costo.
4. Dos vecinas inician rutas de costo mínimo: va a la de menor id.
5. Una puerta de su ruta se cierra entre dos turnos: en el turno siguiente decide como si calculara desde cero.
6. Un actor de velocidad alta atraviesa una salida de costo 1: el intervalo es al menos 1.
7. Cambia la velocidad de un actor que atraviesa una salida costosa: el tiempo restante se escala según P1 §2.3.

### Edge Cases

- El límite d = rango permite moverse; sin ruta abierta se espera.
- Un costo 1 nunca produce un intervalo menor que 1.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-CAZ-01**: una salida puede declarar `costo` (entero ≥ 1); si no lo declara vale 100; es igual en ambos sentidos.
- **FR-CAZ-02**: atravesar una salida tiene como costo base el costo de esa salida; el intervalo es `max(1, costo_salida * 100 // velocidad)`.
- **FR-CAZ-03**: la regla de costo de tránsito aplica a todos los actores; atacar, esperar y demás acciones no cambian; errantes y rastreadores conservan su comportamiento.
- **FR-CAZ-04**: el catálogo admite el comportamiento `cazador` con campo `rango` (unidades de costo).
- **FR-CAZ-05**: en su turno el cazador aplica en orden: atacar si comparte sala con el jugador; calcular d; esperar; moverse.
- **FR-CAZ-06**: d es el costo mínimo hasta la sala actual del jugador usando solo salidas abiertas en ese instante.
- **FR-CAZ-07**: si no hay ruta o d > rango, el cazador espera con costo 100.
- **FR-CAZ-08**: si hay ruta y d ≤ rango, se mueve un paso por una ruta de costo d; la acción cuesta lo que la salida.
- **FR-CAZ-09**: desempate: entre vecinas v con `costo(u,v) + dist(v, jugador) = d`, va a la de menor id, siempre, incluso con muchas rutas de igual costo.
- **FR-CAZ-10**: el cazador conoce el esqueleto completo y el estado actual de las puertas, ignora la niebla, no abre puertas y no depende de si el contenido de una sala fue descargado.
- **FR-CAZ-11**: la decisión en cada turno es idéntica a la de un cálculo desde cero en ese instante.
- **FR-CAZ-12**: un cambio de velocidad en medio de un movimiento escala el tiempo restante según P1 §2.3.
- **FR-CAZ-13**: la vista muestra los costos de las salidas de la sala actual y distingue a los cazadores de otros enemigos (P2 §7.3).
- **FR-CAZ-14** (rendimiento): ciclo de eventos ≤ 20 ms con decenas de cazadores activos; el costo de una decisión crece con la región dentro del rango, no con el tamaño de la cripta.
- **FR-CAZ-15** (medición): `--bench` compara un cazador frente a muchos, rango pequeño frente a grande, cálculo compartido frente a individual, y reutilización frente a recálculo siempre, con puertas estables e inestables.

### Key Entities

- Salida: conecta dos salas y tiene costo y estado de puerta compartidos en ambos sentidos.
- Cazador: enemigo con sala, velocidad y rango expresado en costo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-CAZ-01**: Ciclo de eventos de como máximo 20 ms con decenas de cazadores activos.
- **SC-CAZ-02**: Con rango pequeño, el trabajo depende de la región dentro del rango y no del tamaño total de la cripta.
- **SC-CAZ-03**: Todas las decisiones coinciden con el resultado desde cero, incluidos empates y cambios de puertas.

## Assumptions

- Fuentes: [guía de parte II](../../docs/CRIPTA%20Parte%20II%20gu%C3%ADa%20y%20divisi%C3%B3n%20del%20trabajo.md), [P1](../../docs/enunciado.md) y [constitución](../../.specify/memory/constitution.md).
- La guía es un resumen y una propuesta de trabajo, no el enunciado íntegro de P2. Sus referencias deben contrastarse con ese enunciado cuando esté disponible.
- Los requisitos copiados de la guía son la base solicitada; los supuestos siguientes son propuestas explícitas para revisión, no nuevas reglas oficiales.
- Se conserva P1 para combate, activación y reajuste del tiempo restante al cambiar velocidad.
- Puerta abierta significa abierta al resolver el turno; un cierre pendiente no equivale a un cierre ya ejecutado.
- No se añade un límite de ocupación de salas que no figure en P1.
- Los límites temporales son criterios de aceptación pendientes de medición; este documento no afirma que ya se cumplan. La máquina y carga reproducible se precisarán al planificar.

### Descripción de entrada conservada

Capacidad: terreno y cazador. Desde el punto de vista del juego, las salidas ahora tienen un costo de tránsito y aparece un enemigo que persigue al jugador por la ruta más barata.

Cada salida puede declarar un costo, entero mayor o igual que 1. Si no lo declara, vale 100. El costo es el mismo en ambos sentidos. Atravesar una salida es una acción cuyo costo base es el de esa salida (en lugar del 100 fijo de P1 §2.3). El intervalo es max(1, costo_salida * 100 // velocidad). Aplica a todos los actores. El costo de atacar, esperar y las demás acciones no cambia. Errantes y rastreadores solo cambian lo que tarda su movimiento.

Se agrega el comportamiento de enemigo «cazador», con un campo rango (entero, en unidades de costo). En su turno, en orden: (1) si comparte sala con el jugador, ataca (P1 §2.8); (2) si no, considera el costo mínimo d de llegar a la sala actual del jugador sumando el costo de cada salida recorrida, usando solo salidas abiertas en ese instante; (3) si no hay ruta, o si d > rango, espera (costo 100); (4) si hay, se mueve un paso por una ruta de costo d, y la acción cuesta lo que la salida que atraviesa.

Desempate: sea u la sala del cazador; entre las vecinas v tales que costo(u,v) + dist(v, jugador) = d, se mueve a la de menor id, sin importar cómo se calcule.

El cazador conoce el esqueleto completo (con costos) y el estado actual de todas las puertas. No le afecta la niebla de guerra del jugador, no abre puertas cerradas y su decisión nunca depende de si el contenido de una sala ya fue descargado.

Equivalencia observable: la decisión en cada turno debe ser idéntica a la que daría un cálculo desde cero en ese instante, aunque entre turnos se abran o cierren puertas, se mueva el jugador, mueran otros actores o cambien velocidades. Se pueden reutilizar cálculos anteriores solo si nunca cambia la decisión.

Rendimiento: el ciclo de eventos entre dos decisiones del jugador toma como máximo 20 ms con decenas de cazadores activos. La decisión de un cazador de rango pequeño no debe costar proporcionalmente al tamaño de la cripta, sino a la región dentro de su rango.
