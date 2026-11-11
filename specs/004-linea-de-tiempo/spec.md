# Feature Specification: Línea de tiempo

**Feature Branch**: sin rama dedicada; carpeta `004-linea-de-tiempo` (independiente de la rama Git)

**Created**: 2026-11-05

**Status**: Implementación004 validada offline el2026-11-10; contratos aprobados, mediciones y capturas registradas. Recorrido manual humano de interfaz pendiente (T033).

**Input**: descripción del usuario y bloque 004 de la guía de parte II.

## Clarifications

### Session 2026-11-08

- Q: ¿Qué debe contar como una acción numerada de la línea de tiempo? → A: Cada acción aceptada que cambia la partida; cada paso automático cuenta por separado, y el uso aceptado de un pergamino también cuenta. Las consultas y acciones rechazadas no cuentan.
- Q: Después de que un pergamino elimina acciones de la línea, ¿cómo deben numerarse las acciones que sobreviven? → A: Renumerar la línea vigente consecutivamente desde 1, incluyendo el uso aceptado del pergamino como la siguiente acción.
- Q: Al cargar un archivo de partida de P1, ¿qué debe hacer la línea de tiempo? → A: Rechazar el archivo con un mensaje claro de incompatibilidad.
- Q: ¿Qué debe pasar al cargar un guardado P2 creado antes de 004, que aún no tiene historial persistido? → A: Rechazarlo con un mensaje explícito de incompatibilidad.
- Q: Si, tras usar un pergamino, hay más de una decisión del jugador en el mismo tiempo t, ¿qué estado debe mostrar `historia <t>`? → A: El estado justo antes de la primera decisión en t de la línea vigente, después de los eventos automáticos de ese instante.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Línea de tiempo (Priority: P1)

Como jugador, quiero consultar estados pasados sin alterar la partida ni el retroceso disponible.

**Why this priority**: es el comportamiento central de esta capacidad y permite verificar su valor de forma aislada con una partida preparada.

**Independent Test**: ejecutar los escenarios siguientes en una cripta preparada y comparar el resultado observable con el esperado, sin depender de otras capacidades salvo las dependencias indicadas.

**Acceptance Scenarios**:

Los escenarios1–6 se contrastaron con el Apéndice B oficial; el escenario7 recoge el acuerdo local de compatibilidad. No se declaran ejecutados.

1. `historia <t>` con t mayor que el reloj actual: se rechaza.
2. `historia` después de usar un pergamino: no muestra las acciones revertidas.
3. Varios eventos ocurren en el mismo instante t: `historia <t>` muestra el estado después de todos ellos.
4. `historia` no consume tiempo virtual, no se registra en `partida.log` y no modifica el historial de retroceso.
5. `--replay partida.log --hasta t` con t posterior al final: muestra el estado final e indica que la partida terminó antes.
6. Se carga un archivo de partida de la parte 1: se rechaza con un mensaje explícito de incompatibilidad.
7. Se carga un archivo P2 anterior a 004 que no conserva historial: se rechaza con un mensaje explícito de incompatibilidad.

### Edge Cases

- Varios eventos en t se incluyen todos antes de mostrar el estado.
- Consultar el futuro en partida se rechaza; reproducir más allá del final muestra el estado final y lo indica.
- Retroceder elimina de la línea las acciones revertidas.
- Los guardados P1 y los P2 previos a 004 sin historial se rechazan explícitamente.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-LIN-01**: el estado en el instante t es el posterior a todos los eventos automáticos con tiempo ≤ t y anterior a la primera decisión del jugador en t en la línea vigente. Si el reloj se repite tras un pergamino, `historia <t>` devuelve ese mismo punto único; `historia #k` distingue acciones concretas.
- **FR-LIN-02**: `historia <t>` y `historia #k` (justo antes de la acción k del jugador) están disponibles en partida. El número cuenta las acciones aceptadas que cambian la partida; cada paso automático de «ir a» y cada uso aceptado de un pergamino cuentan por separado. Las consultas y acciones rechazadas no cuentan.
- **FR-LIN-03**: el resumen incluye como mínimo reloj, sala del jugador, vida y estadísticas, inventario, efectos activos, enemigos de esa sala con su vida y el mapa conocido en ese momento.
- **FR-LIN-04**: la consulta no consume tiempo virtual, no se registra como acción en `partida.log` y no altera el estado del juego ni el historial de retroceso.
- **FR-LIN-05**: consultar un instante posterior al reloj actual se rechaza.
- **FR-LIN-06**: `--replay partida.log --hasta <t>` imprime el mismo resumen sin instanciar la vista; si t es posterior al final, muestra el estado final e indica que la partida terminó antes.
- **FR-LIN-07**: las acciones revertidas con un pergamino dejan de existir en la línea. La línea vigente se renumera consecutivamente desde 1 e incluye el uso aceptado del pergamino como la acción siguiente a las que sobrevivieron.
- **FR-LIN-08**: hay como máximo un punto de control cada K acciones del jugador; K se configura con `--checkpoint-cada` y su valor por defecto se justifica con mediciones.
- **FR-LIN-09**: una consulta aplica o deshace cambios de a lo sumo K acciones del jugador.
- **FR-LIN-10**: fuera de los puntos de control solo se guarda lo necesario para reconstruir cambios; la memoria crece con los cambios más un punto cada K acciones.
- **FR-LIN-11**: el estado reconstruido es idéntico al que tuvo la partida original en ese instante (determinismo).
- **FR-LIN-12**: guardar y cargar conserva la línea completa; los archivos P1 y los P2 anteriores a 004 que carecen de historial se rechazan con un mensaje explícito de incompatibilidad, nunca se cargan en silencio.
- **FR-LIN-13** (rendimiento): con al menos 5 000 acciones y K por defecto, el máximo observado entre 1 000 consultas medidas de `historia`, luego de 100 calentamientos, debe ser ≤50 ms. Usar un pergamino recorta la línea sin recorrer toda la historia.
- **FR-LIN-14** (medición): `--bench` mide memoria y tiempo de consulta con al menos tres valores de K y contra la alternativa sin puntos de control.

- **FR-LIN-15 (solicitud del usuario, 2026-11-10)**: la interfaz gráfica permite explorar la historia mediante un panel visual integrado con el juego, con selección de tiempo o acción, navegación y secciones jerarquizadas para estadísticas, inventario, efectos, enemigos y mapa histórico. Identifica claramente el instante consultado y el estado actual; consultar no modifica ni revierte la partida.
- **FR-LIN-16 (solicitud del usuario, 2026-11-10)**: la interfaz histórica mantiene la paleta, tipografía, escala y patrones de interacción existentes; usa una retícula base de8 px para espaciados, márgenes internos/externos; todos los paneles, controles, barras y nodos usan esquinas rectas. Texto y contenido deben adaptarse al espacio disponible sin recortes ni superposiciones. Selección, foco, estados vacíos y errores deben ser comprensibles sin depender solo del color.

### Key Entities

- Instante histórico: estado después de los eventos de tiempo menor o igual a t, antes de una decisión del jugador en ese instante.
- Acción numerada: acción del jugador cuya situación previa puede consultarse.
- Punto de control: estado completo separado según el intervalo K.
- Resumen histórico: reloj, sala, vida, estadísticas, inventario, efectos, enemigos locales y mapa conocido.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-LIN-01**: El máximo observado en al menos 1 000 consultas medidas de `historia`, luego de 100 calentamientos y con al menos 5 000 acciones y K por defecto, es ≤50 ms.
- **SC-LIN-02**: Cada consulta aplica o deshace cambios de como máximo K acciones.
- **SC-LIN-03**: Memoria proporcional a los cambios más un punto de control cada K acciones; se comparan al menos tres K y la alternativa sin puntos.
- **SC-LIN-04**: La consulta no altera la partida; retroceder recorta la línea sin recorrer toda la historia; guardar y cargar conserva la línea completa.

### Aceptación de interfaz solicitada

1. Abrir historia desde un control visible del juego; reconocer inmediatamente que se está consultando el pasado y qué tiempo/acción está seleccionado.
2. Navegar por acciones y consultar un tiempo concreto con teclado y ratón; el foco se distingue y Escape cierra el panel devolviendo el control al juego.
3. Ver estadísticas agrupadas, inventario/efectos y enemigos con los recursos visuales existentes, y el mapa conocido del instante consultado. No usar el mapa actual para representar el pasado.
4. Sin acciones, sin enemigos o sin efectos, mostrar estados vacíos explícitos; ante una consulta inválida, conservar selección/resumen válido y mostrar un mensaje junto al control afectado.
5. Con nombres largos y listas grandes, desplazamiento o ajuste mantiene los controles utilizables en los tamaños de ventana admitidos por la aplicación; el panel impide movimiento por proximidad o pasos automáticos mientras tiene foco.
6. Inspeccionar capturas y recorrer controles reales antes de dar por aprobada la interfaz, además de las pruebas automatizadas.

## Assumptions

- Fuentes: [guía de parte II](../../docs/CRIPTA%20Parte%20II%20gu%C3%ADa%20y%20divisi%C3%B3n%20del%20trabajo.md), [P1](../../docs/enunciado.md) y [constitución](../../.specify/memory/constitution.md).
- Fuente normativa: [Cripta Parte II](../../docs/Cripta%20Parte%20II.md), §§3.6,5.5,6.1–6.3 y Apéndice B; contraste registrado en research.md. La guía es complementaria.
- Las aclaraciones locales y el protocolo de100 calentamientos/1000 consultas complementan el enunciado; no se atribuyen a este como reglas oficiales.
- Cada paso de ir a cuenta como una acción para K y para historia #k; también cuenta cada uso aceptado de un pergamino. Las consultas y acciones rechazadas quedan fuera del conteo.
- Las acciones contadas se numeran consecutivamente desde 1 en la línea vigente. Tras un retroceso, las que sobreviven se renumeran y el uso aceptado del pergamino se agrega al final; #0, índices inexistentes y tiempos negativos o no enteros se rechazan sin efectos.
- K debe ser entero mayor o igual que 1; su valor por defecto se decide en el plan con mediciones de al menos tres valores.
- Si el reloj se repite tras un pergamino, `historia <t>` resuelve el instante antes de la primera decisión en ese tiempo de la línea vigente; `historia #k` permite consultar un punto de acción preciso.
- El estado inicial puede conservarse como origen de reconstrucción; no autoriza copias completas por acción.
- Depende del conocimiento definido en 002; se conserva el límite de cinco acciones del pergamino de P1.
- La representación concreta del resumen se fija al planificar, preservando los comportamientos exigidos. P1 y los guardados P2 anteriores a 004 que no persisten historial no se migran porque no contienen una línea reconstruible.
- Los límites temporales son criterios de aceptación pendientes de medición; este documento no afirma que ya se cumplan. La máquina y carga reproducible se precisarán al planificar.

### Descripción de entrada conservada

Capacidad: línea de tiempo. El pergamino de retroceso (P1 §2.11) sigue limitado a 5 acciones. La línea de tiempo es independiente: permite consultar, sin modificar la partida, el estado en cualquier instante desde el inicio.

Estado en el instante t: el estado después de ejecutar todos los eventos automáticos con tiempo menor o igual que t y justo antes de la primera decisión del jugador en ese tiempo de la línea vigente. Si el reloj se repite tras un pergamino, se conserva un único resultado por tiempo; `historia #k` permite distinguir acciones concretas.

Consulta en partida: el comando «historia <t>» o «historia #k» (estado justo antes de la acción número k del jugador) muestra como mínimo: reloj, sala del jugador, vida y estadísticas, inventario, efectos activos, enemigos de esa sala con su vida, y el mapa conocido en ese momento. La consulta no consume tiempo virtual, no se registra como acción y no altera ningún estado del juego ni del historial de retroceso. Consultar un instante posterior al reloj actual se rechaza.

Consulta sin interacción: --replay partida.log --hasta <t> reproduce la partida hasta t e imprime el mismo resumen sin instanciar la vista. Si t es posterior al final de la partida, muestra el estado final e indica que la partida terminó antes.

Interacción con el retroceso: las acciones revertidas con un pergamino dejan de existir en la línea; la línea describe la historia tal como quedó.

Restricción de memoria: se permiten copias completas del estado (puntos de control), pero no más de una cada K acciones del jugador. K se configura con --checkpoint-cada K; el valor por defecto lo escoge el grupo y lo justifica con mediciones. Una consulta no puede requerir aplicar o deshacer cambios de más de K acciones del jugador. Fuera de los puntos de control solo se almacena la información necesaria para reconstruir los cambios. La memoria total crece con la cantidad de cambios ocurridos más un punto de control cada K acciones, nunca con acciones por tamaño del estado.

Persistencia: guardar y cargar conserva la línea completa. Los archivos P1 y los guardados P2 previos a 004 que carecen de historial se rechazan con un error explícito; nunca se cargan en silencio.

Rendimiento: el máximo observado entre al menos 1 000 consultas medidas de «historia», luego de 100 calentamientos, es ≤50 ms en una partida de al menos 5 000 acciones con K por defecto. También se miden memoria y tiempo con al menos tres valores de K y contra la alternativa sin puntos de control.
