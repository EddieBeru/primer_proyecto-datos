# Feature Specification: Niebla de guerra e ir a

**Feature Branch**: sin rama dedicada; carpeta `002-niebla-ir-a` (independiente de la rama Git)

**Created**: 2026-11-05

**Status**: Draft — pendiente de revisión con `$speckit-clarify`

**Input**: descripción del usuario y bloque 002 de la guía de parte II.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Niebla de guerra e ir a (Priority: P1)

Como jugador, quiero consultar solo lo que conozco y viajar automáticamente sin recibir información oculta.

**Why this priority**: es el comportamiento central de esta capacidad y permite verificar su valor de forma aislada con una partida preparada.

**Independent Test**: ejecutar los escenarios siguientes en una cripta preparada y comparar el resultado observable con el esperado, sin depender de otras capacidades salvo las dependencias indicadas.

**Acceptance Scenarios**:

Los casos siguientes conservan los escenarios atribuidos al Apéndice B por la guía; cada uno especifica condición, acción y resultado esperado.

1. `ir a` hacia una sala no explorada: se rechaza y no consume tiempo.
2. El mapa recuerda abierta una puerta que en realidad está cerrada: al observarla, el mapa se actualiza y la ruta se recalcula; si no queda ruta, el viaje se detiene sin consumir tiempo adicional.
3. `ir a` entra a una sala con enemigos dormidos: se activan según P1 §2.4 y el viaje se detiene.
4. Con la antorcha encendida, entrar a una sala explora sus vecinas sin activar sus enemigos ni trampas.
5. Un pergamino revierte una entrada con antorcha encendida: las salas exploradas por la antorcha vuelven a su estado anterior.
6. Un pergamino durante un viaje: revierte solo el último paso y el viaje no continúa.

### Edge Cases

- Destino actual: termina inmediatamente sin movimiento ni consumo de tiempo.
- Una puerta recordada abierta puede estar cerrada; observarla actualiza el conocimiento antes del siguiente intento.
- El daño de trampas y efectos también detiene el viaje.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-NIE-01**: cada sala está para el jugador en exactamente uno de tres estados: explorada, avistada o desconocida.
- **FR-NIE-02**: la sala inicial está explorada desde el instante 0.
- **FR-NIE-03**: de una sala explorada se conoce nombre, salidas, costo de cada salida y estado de sus puertas según la última observación.
- **FR-NIE-04**: de una sala avistada solo se conoce que existe.
- **FR-NIE-05**: el jugador observa una puerta al estar en cualquiera de las dos salas que conecta; el mapa recuerda el último estado observado aunque cambie después.
- **FR-NIE-06**: con la antorcha encendida, al entrar a una sala quedan exploradas todas sus vecinas por cualquier salida; se revela nombre y salidas, no contenido; no se activan enemigos ni trampas.
- **FR-NIE-07**: la vista y «ir a» se derivan solo del conocimiento del jugador.
- **FR-NIE-08**: el conocimiento se guarda en el archivo de partida, se revierte con el pergamino y forma parte de la línea de tiempo.
- **FR-NIE-09**: existe un comando para ver el mapa conocido (salas exploradas, sus salidas, salas avistadas).
- **FR-NIE-10**: «ir a» rechaza destinos no explorados sin consumir tiempo.
- **FR-NIE-11**: la ruta usa solo salas exploradas y salidas recordadas abiertas; minimiza la suma de costos; desempate por menor id en el primer paso.
- **FR-NIE-12**: cada paso es una acción completa del jugador que consume tiempo según FR-CAZ-02, con eventos del reloj entre pasos.
- **FR-NIE-13**: la ruta se recalcula antes de cada paso con el conocimiento vigente.
- **FR-NIE-14**: el viaje se detiene al llegar, al entrar a una sala con enemigos (activos o dormidos), al recibir daño o al no existir ruta conocida.
- **FR-NIE-15**: «ir a» no abre puertas aunque el jugador tenga la llave.
- **FR-NIE-16**: en `partida.log` cada paso es un movimiento individual y «ir a» queda como comentario.
- **FR-NIE-17**: el pergamino revierte solo el último paso y el viaje no continúa.
- **FR-NIE-18**: la interfaz muestra por qué se detuvo un viaje.
- **FR-NIE-19** (rendimiento): un paso de «ir a» ≤ 5 ms con el mapa conocido completo; explorar cuesta proporcionalmente a las salas reveladas.
- **FR-NIE-20** (medición): `--bench` mide consultas al mapa conocido y el cálculo de «ir a».

### Key Entities

- Conocimiento de sala: estado explorada, avistada o desconocida y datos revelados.
- Memoria de puerta: último estado observado por el jugador.
- Viaje: destino explorado y sucesión de movimientos ordinarios.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-NIE-01**: Calcular un paso tarda como máximo 5 ms con el mapa conocido completo de la cripta de referencia.
- **SC-NIE-02**: Revelar salas cuesta proporcionalmente a las salas reveladas, sin recorrer el mapa conocido completo.
- **SC-NIE-03**: La consulta del mapa y el viaje no revelan información desconocida; guardar, cargar y retroceder conservan el conocimiento correspondiente.

## Assumptions

- Fuentes: [guía de parte II](../../docs/CRIPTA%20Parte%20II%20gu%C3%ADa%20y%20divisi%C3%B3n%20del%20trabajo.md), [P1](../../docs/enunciado.md) y [constitución](../../.specify/memory/constitution.md).
- La guía es un resumen y una propuesta de trabajo, no el enunciado íntegro de P2. Sus referencias deben contrastarse con ese enunciado cuando esté disponible.
- Los requisitos copiados de la guía son la base solicitada; los supuestos siguientes son propuestas explícitas para revisión, no nuevas reglas oficiales.
- Las vecinas reveladas por antorcha cuentan como exploradas y sus salidas hacen avistados sus destinos, sin propagación adicional de exploración.
- Apagar la antorcha no borra conocimiento adquirido; solo impide revelaciones futuras por ese efecto.
- Enemigos muertos no detienen el viaje; la condición se refiere a enemigos vivos activos o dormidos.
- Las causas de detención se presentan mediante un mensaje comprensible, sin imponer formato visual.
- Depende de los costos y desempate de 001 y se integra con la persistencia y la historia de 004.
- Los límites temporales son criterios de aceptación pendientes de medición; este documento no afirma que ya se cumplan. La máquina y carga reproducible se precisarán al planificar.

### Descripción de entrada conservada

Capacidad: niebla de guerra y viaje automático «ir a». El jugador ya no ve el mapa completo, solo lo que ha explorado, y puede viajar automáticamente dentro de ese conocimiento.

Cada sala está, para el jugador, en uno de tres estados. Explorada: entró al menos una vez (la sala inicial lo está desde el instante 0); conoce nombre, salidas, costo de cada salida y estado de sus puertas según la última observación. Avistada: no explorada, pero es destino de una salida de una sala explorada; solo se sabe que existe una sala detrás. Desconocida: ninguna de las anteriores.

Memoria de puertas: el jugador observa una puerta cuando está en cualquiera de las dos salas que conecta. El mapa del jugador recuerda el estado de cada puerta según su última observación, aunque haya cambiado después (una puerta con cierre automático puede figurar abierta en el mapa y estar cerrada en realidad).

Antorcha (P1 §2.7): mientras esté encendida, al entrar a una sala quedan exploradas todas sus vecinas, por cualquier salida, abierta o cerrada. Eso revela nombre y salidas, no el contenido, y no activa enemigos ni trampas.

Todo lo que la vista muestra y lo que usa «ir a» se deriva exclusivamente del conocimiento del jugador (el programa puede descargar el esqueleto completo como infraestructura). El conocimiento es estado del juego: se guarda en el archivo de partida, se revierte con el pergamino de retroceso y forma parte de la línea de tiempo. Debe existir un comando para ver el mapa conocido: salas exploradas, sus salidas y las salas avistadas.

«ir a <sala>» lleva al jugador a una sala explorada con movimientos ordinarios. La ruta usa solo salas exploradas y salidas que el mapa recuerda abiertas, minimiza la suma de costos y desempata como el cazador (primer paso hacia la vecina de menor id). Cada paso es una acción completa del jugador: consume tiempo según el costo de la salida y entre paso y paso ocurren los eventos del reloj. La ruta se recalcula antes de cada paso con el conocimiento vigente. El viaje se detiene cuando: llega al destino; entra a una sala con enemigos (activos o dormidos); recibe daño; o deja de existir una ruta conocida. No abre puertas aunque tenga la llave. En partida.log cada paso se registra como un movimiento individual y la orden «ir a» como comentario. El pergamino de retroceso revierte solo el último paso.

Rendimiento: un paso de «ir a» se calcula en ≤ 5 ms con el mapa conocido completo de la cripta de referencia; explorar nuevas salas cuesta proporcionalmente a las salas reveladas, no al tamaño del mapa conocido.
