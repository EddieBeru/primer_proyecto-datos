# Feature Specification: Niebla de guerra e ir a

**Feature Branch**: sin rama dedicada; carpeta `002-niebla-ir-a` (independiente de la rama Git)

**Created**: 2026-11-05

**Status**: Aclarada para planificación — pendiente de contraste con el enunciado íntegro de P2

**Input**: descripción del usuario y bloque 002 de la guía de parte II.

## Clarifications

### Session 2026-11-05

- Q: Si la antorcha revela una sala vecina sin entrar en ella, ¿también revela el estado de sus puertas hacia otras salas? → A: No. Revela nombre, salidas y costos; las puertas no observadas presencialmente quedan con estado desconocido y «ir a» no las considera abiertas. Conserva la última observación de las puertas ya conocidas.

### Session 2026-11-06

- Q: Si el jugador ya está en una sala con enemigos vivos cuando ordena «ir a», ¿puede comenzar el viaje? → A: No. El viaje no inicia y se muestra el motivo sin consumir tiempo; el jugador puede moverse manualmente.
- Q: Al encender la antorcha dentro de una sala, ¿se revelan inmediatamente sus vecinas o hay que moverse primero? → A: Se revelan inmediatamente al encenderla y también al entrar en otras salas mientras siga encendida, con las mismas restricciones de revelación.
- Q: Durante «ir a», ¿el jugador puede cancelar voluntariamente el viaje entre dos pasos? → A: Sí. Puede cancelar después de completar el cambio de sala y sus eventos, antes del siguiente movimiento automático. Cancelar no consume tiempo ni deshace movimientos; recupera el control manual.

### Session 2026-11-08 — ajustes aceptados tras análisis

- La revelación tiene costo esperado amortizado proporcional a los registros consultados o modificados. Las operaciones ordinarias no barren el mapa conocido; las expansiones del índice pueden recorrer sus registros y deben incluirse en las mediciones. El límite de 5 ms para calcular un paso no cambia. Este acuerdo sigue pendiente de contraste con el enunciado íntegro P2.
- Consultar mapa, foto, inventario o ayuda conserva el viaje. Una acción manual lo cancela antes de procesarse; guardar y pausar también lo cancelan. Cargar solo cancela al instalar correctamente la partida; una carga fallida conserva el viaje anterior.
- La entrega aislada de 002 puede verificarse con falsos, pero la aceptación completa de FR-NIE-08 requiere comprobar el conocimiento histórico integrado con 004, incluida su reconstrucción, retroceso y conservación al guardar/cargar.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Niebla de guerra e ir a (Priority: P1)

Como jugador, quiero consultar solo lo que conozco y viajar automáticamente sin recibir información oculta.

**Why this priority**: es el comportamiento central de esta capacidad y permite verificar su valor de forma aislada con una partida preparada.

**Independent Test**: ejecutar los escenarios siguientes en una cripta preparada y comparar el resultado observable con el esperado, sin depender de otras capacidades salvo las dependencias indicadas.

**Acceptance Scenarios**:

Los casos 1–6 conservan los escenarios atribuidos al Apéndice B por la guía; los posteriores documentan las aclaraciones acordadas. Cada uno especifica condición, acción y resultado esperado.

1. `ir a` hacia una sala no explorada: se rechaza y no consume tiempo.
2. El mapa recuerda abierta una puerta que en realidad está cerrada: al observarla, el mapa se actualiza y la ruta se recalcula; si no queda ruta, el viaje se detiene sin consumir tiempo adicional.
3. `ir a` entra a una sala con enemigos dormidos: se activan según P1 §2.4 y el viaje se detiene.
4. Con la antorcha encendida, entrar a una sala explora sus vecinas sin activar sus enemigos ni trampas.
5. Un pergamino revierte una entrada con antorcha encendida: las salas exploradas por la antorcha vuelven a su estado anterior.
6. Un pergamino durante un viaje: revierte solo el último paso y el viaje no continúa.
7. La antorcha revela una sala vecina B y su salida hacia C, cuya puerta nunca fue observada presencialmente: se conocen nombre, salidas y costos de B, pero el estado de esa puerta se muestra desconocido y «ir a» no la usa. Si ya existía una observación de esa puerta, se conserva sin actualizarla a distancia.
8. El jugador está en una sala con enemigos vivos y ordena «ir a» hacia otra sala explorada: el viaje no inicia, se muestra el motivo y no transcurre tiempo virtual; sigue disponible el movimiento manual ordinario. Si solo hay enemigos muertos, esta condición no impide el viaje.
9. El jugador enciende una antorcha en la sala actual: sus vecinas quedan exploradas inmediatamente, por salidas abiertas o cerradas, sin revelar contenido, observar puertas a distancia ni activar enemigos o trampas de esas vecinas. No es necesario moverse para obtener esa revelación.
10. Un pergamino revierte el encendido de la antorcha: el conocimiento adquirido por ese encendido vuelve a su estado anterior, conforme a las reglas de retroceso de P1.
11. Durante un viaje de 2 a 12 por 2 → 5 → 8 → 12, el jugador cancela después del paso de 2 a 5 y sus eventos: permanece en 5, no se ejecuta el paso a 8 y recupera el control manual. La cancelación no consume tiempo adicional ni revierte el cruce a 5.

### Edge Cases

- Destino actual: termina inmediatamente sin movimiento ni consumo de tiempo.
- Una puerta recordada abierta puede estar cerrada; observarla actualiza el conocimiento antes del siguiente intento.
- El daño de trampas y efectos también detiene el viaje.
- Cancelar un viaje no interrumpe una acción del motor a medio ejecutar ni evita sus eventos pendientes; se hace efectivo entre pasos completos.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-NIE-01**: cada sala está para el jugador en exactamente uno de tres estados: explorada, avistada o desconocida.
- **FR-NIE-02**: la sala inicial está explorada desde el instante 0.
- **FR-NIE-03**: de una sala explorada se conoce nombre, salidas y costo de cada salida. De sus puertas se conserva el estado según la última observación presencial; si nunca se observaron, su estado figura como desconocido.
- **FR-NIE-04**: de una sala avistada solo se conoce que existe.
- **FR-NIE-05**: el jugador observa una puerta al estar en cualquiera de las dos salas que conecta; el mapa recuerda el último estado observado aunque cambie después.
- **FR-NIE-06**: al encender la antorcha quedan exploradas inmediatamente todas las vecinas de la sala actual, por cualquier salida abierta o cerrada; la misma revelación ocurre al entrar a una sala mientras la antorcha siga encendida. Se revela nombre, salidas y costos, no contenido; no se activan enemigos ni trampas de las salas reveladas a distancia. La revelación no observa las puertas a distancia: conserva su última observación presencial o el estado desconocido si no existe ninguna.
- **FR-NIE-07**: la vista y «ir a» se derivan solo del conocimiento del jugador.
- **FR-NIE-08**: el conocimiento se guarda en el archivo de partida, se revierte con el pergamino y forma parte de la línea de tiempo. Deshacer el encendido de la antorcha restaura también el conocimiento previo a la revelación de sus vecinas.
- **FR-NIE-09**: existe un comando para ver el mapa conocido (salas exploradas, sus salidas, salas avistadas).
- **FR-NIE-10**: «ir a» rechaza destinos no explorados sin consumir tiempo.
- **FR-NIE-11**: la ruta usa solo salas exploradas y salidas recordadas abiertas; excluye puertas con estado desconocido; minimiza la suma de costos; desempate por menor id en el primer paso.
- **FR-NIE-12**: cada paso es una acción completa del jugador que consume tiempo según FR-CAZ-02, con eventos del reloj entre pasos.
- **FR-NIE-13**: la ruta se recalcula antes de cada paso con el conocimiento vigente.
- **FR-NIE-14**: el viaje se detiene al llegar, al entrar a una sala con enemigos vivos (activos o dormidos), al recibir daño o al no existir ruta conocida. Si ya hay enemigos vivos en la sala de partida, no inicia el viaje: se muestra el motivo sin consumir tiempo, y el movimiento manual ordinario sigue disponible. Los enemigos muertos no impiden iniciar ni continuar el viaje.
- **FR-NIE-15**: «ir a» no abre puertas aunque el jugador tenga la llave.
- **FR-NIE-16**: en `partida.log` cada paso es un movimiento individual y «ir a» queda como comentario.
- **FR-NIE-17**: el pergamino revierte solo el último paso y el viaje no continúa.
- **FR-NIE-18**: la interfaz muestra por qué se detuvo un viaje.
- **FR-NIE-19** (rendimiento): calcular un paso de «ir a» ≤ 5 ms con el mapa conocido completo. Revelar salas tiene costo esperado amortizado proporcional a los registros de salas y puertas consultados o modificados; las operaciones ordinarias no recorren el mapa conocido completo. Las expansiones del índice pueden recorrer sus registros y deben incluirse en las mediciones.
- **FR-NIE-20** (medición): `--bench` mide consultas al mapa conocido y el cálculo de «ir a».
- **FR-NIE-21**: el jugador puede cancelar voluntariamente «ir a» entre pasos, después de completar el movimiento anterior y sus eventos, antes del siguiente movimiento automático. La cancelación detiene la continuación automática, devuelve el control manual, no consume tiempo virtual ni deshace movimientos; la interfaz muestra el motivo de detención.

### Key Entities

- Conocimiento de sala: estado explorada, avistada o desconocida y datos revelados.
- Memoria de puerta: último estado observado presencialmente por el jugador, o estado desconocido si nunca la observó; independiente del estado de exploración de las salas.
- Viaje automático «ir a»: destino explorado y sucesión de cambios de sala mediante movimientos ordinarios; cada paso incluye sus eventos hasta la siguiente decisión del jugador. Se distingue del desplazamiento visual dentro de una sala y del cruce manual de puertas por proximidad.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-NIE-01**: Calcular un paso tarda como máximo 5 ms con el mapa conocido completo de la cripta de referencia.
- **SC-NIE-02**: Revelar salas tiene costo esperado amortizado proporcional a los registros de salas y puertas consultados o modificados. Las operaciones ordinarias no recorren el mapa conocido completo; las mediciones incluyen el trabajo de las expansiones del índice, que sí pueden recorrer sus registros.
- **SC-NIE-03**: La consulta del mapa y el viaje no revelan información desconocida; guardar, cargar y retroceder conservan el conocimiento correspondiente.

## Assumptions

- Fuentes: [guía de parte II](../../docs/CRIPTA%20Parte%20II%20gu%C3%ADa%20y%20divisi%C3%B3n%20del%20trabajo.md), [P1](../../docs/enunciado.md) y [constitución](../../.specify/memory/constitution.md).
- La guía es un resumen y una propuesta de trabajo, no el enunciado íntegro de P2. Sus referencias deben contrastarse con ese enunciado cuando esté disponible.
- Los requisitos copiados de la guía son la base solicitada; las aclaraciones registradas son acuerdos del usuario para planificar, no nuevas reglas oficiales. Los supuestos restantes se mantienen explícitos y deben contrastarse con el enunciado íntegro de P2.
- Las vecinas reveladas por antorcha cuentan como exploradas y sus salidas hacen avistados sus destinos, sin propagación adicional de exploración.
- Apagar la antorcha no borra conocimiento adquirido; solo impide revelaciones futuras por ese efecto.
- Enemigos muertos no detienen el viaje; la condición se refiere a enemigos vivos activos o dormidos.
- Las causas de detención se presentan mediante un mensaje comprensible, sin imponer formato visual.
- «Ir a» agrega viaje automático; el movimiento manual existente por proximidad a una puerta abierta se conserva sin añadir confirmación de cruce. La selección del destino, animación y control concreto de cancelación se definirán en el plan, preservando la posibilidad de cancelar entre pasos.
- Depende de los costos y desempate de 001 y se integra con la persistencia y la historia de 004.
- Los límites temporales son criterios de aceptación pendientes de medición; este documento no afirma que ya se cumplan. La máquina y carga reproducible se precisarán al planificar.

### Descripción de entrada conservada

Texto original de referencia; en caso de diferencias, se aplican las aclaraciones y los requisitos actualizados de esta especificación.

Capacidad: niebla de guerra y viaje automático «ir a». El jugador ya no ve el mapa completo, solo lo que ha explorado, y puede viajar automáticamente dentro de ese conocimiento.

Cada sala está, para el jugador, en uno de tres estados. Explorada: entró al menos una vez (la sala inicial lo está desde el instante 0); conoce nombre, salidas, costo de cada salida y estado de sus puertas según la última observación. Avistada: no explorada, pero es destino de una salida de una sala explorada; solo se sabe que existe una sala detrás. Desconocida: ninguna de las anteriores.

Memoria de puertas: el jugador observa una puerta cuando está en cualquiera de las dos salas que conecta. El mapa del jugador recuerda el estado de cada puerta según su última observación, aunque haya cambiado después (una puerta con cierre automático puede figurar abierta en el mapa y estar cerrada en realidad).

Antorcha (P1 §2.7): mientras esté encendida, al entrar a una sala quedan exploradas todas sus vecinas, por cualquier salida, abierta o cerrada. Eso revela nombre y salidas, no el contenido, y no activa enemigos ni trampas.

Todo lo que la vista muestra y lo que usa «ir a» se deriva exclusivamente del conocimiento del jugador (el programa puede descargar el esqueleto completo como infraestructura). El conocimiento es estado del juego: se guarda en el archivo de partida, se revierte con el pergamino de retroceso y forma parte de la línea de tiempo. Debe existir un comando para ver el mapa conocido: salas exploradas, sus salidas y las salas avistadas.

«ir a <sala>» lleva al jugador a una sala explorada con movimientos ordinarios. La ruta usa solo salas exploradas y salidas que el mapa recuerda abiertas, minimiza la suma de costos y desempata como el cazador (primer paso hacia la vecina de menor id). Cada paso es una acción completa del jugador: consume tiempo según el costo de la salida y entre paso y paso ocurren los eventos del reloj. La ruta se recalcula antes de cada paso con el conocimiento vigente. El viaje se detiene cuando: llega al destino; entra a una sala con enemigos (activos o dormidos); recibe daño; o deja de existir una ruta conocida. No abre puertas aunque tenga la llave. En partida.log cada paso se registra como un movimiento individual y la orden «ir a» como comentario. El pergamino de retroceso revierte solo el último paso.

Rendimiento: un paso de «ir a» se calcula en ≤ 5 ms con el mapa conocido completo de la cripta de referencia; explorar nuevas salas cuesta proporcionalmente a las salas reveladas, no al tamaño del mapa conocido.
