# Feature Specification: Terreno y cazador

**Feature Branch**: `001-terreno-cazador`

**Created**: 2026-11-09

**Status**: Implementada e integrada con002/003/004; pruebas, mediciones y validación CLI --bench completadas el2026-11-16.

**Input**: User description: "Capacidad: terreno y cazador. Desde el punto de vista del juego, las salidas ahora tienen un costo de tránsito y aparece un enemigo que persigue al jugador por la ruta más barata. Cada salida puede declarar un costo, entero mayor o igual que 1. Si no lo declara, vale 100. El costo es el mismo en ambos sentidos. Atravesar una salida es una acción cuyo costo base es el de esa salida (en lugar del 100 fijo de P1 §2.3). El intervalo es max(1, costo_salida * 100 // velocidad). Aplica a todos los actores. El costo de atacar, esperar y las demás acciones no cambia. Errantes y rastreadores solo cambian lo que tarda su movimiento. Se agrega el comportamiento de enemigo «cazador», con un campo rango (entero, en unidades de costo). En su turno, en orden: (1) si comparte sala con el jugador, ataca (P1 §2.8); (2) si no, considera el costo mínimo d de llegar a la sala actual del jugador sumando el costo de cada salida recorrida, usando solo salidas abiertas en ese instante; (3) si no hay ruta, o si d > rango, espera (costo 100); (4) si hay, se mueve un paso por una ruta de costo d, y la acción cuesta lo que la salida que atraviesa. Desempate: sea u la sala del cazador; entre las vecinas v tales que costo(u,v) + dist(v, jugador) = d, se mueve a la de menor id, sin importar cómo se calcule. El cazador conoce el esqueleto completo (con costos) y el estado actual de todas las puertas. No le afecta la niebla de guerra del jugador, no abre puertas cerradas y su decisión nunca depende de si el contenido de una sala ya fue descargado. Equivalencia observable: la decisión en cada turno debe ser idéntica a la que daría un cálculo desde cero en ese instante, aunque entre turnos se abran o cierren puertas, se mueva el jugador, mueran otros actores o cambien velocidades. Se pueden reutilizar cálculos anteriores solo si nunca cambia la decisión. Rendimiento: el ciclo de eventos entre dos decisiones del jugador toma como máximo 20 ms con decenas de cazadores activos. La decisión de un cazador de rango pequeño no debe costar proporcionalmente al tamaño de la cripta, sino a la región dentro de su rango. No mencionar estructuras de datos, clases ni módulos."

## Clarifications

### Session 2026-11-09

- Q: Si el costo mínimo de la ruta hacia el jugador d es exactamente igual al rango del cazador (d == rango), ¿el cazador se mueve o espera? → A: Se mueve. La condición de espera aplica estrictamente cuando d > rango o cuando no existe ninguna ruta abierta; por tanto, d <= rango permite y activa el avance de un paso por la ruta de costo mínimo.
- Q: ¿Qué cuenta exactamente como una salida «abierta en ese instante» para puertas con cierre automático pendiente en la agenda? → A: Cuenta el estado efectivo de la puerta en el instante exacto del reloj virtual en que se resuelve el turno del cazador. Si la puerta figura como abierta, es transitable y se usa para calcular d; un cierre automático programado para un instante futuro no la bloquea anticipadamente.
- Q: ¿El costo total de la ruta d incluye el costo de la salida que entra a la sala actual del jugador? → A: Sí. La distancia d es la suma acumulada de los costos de todas las salidas recorridas en la trayectoria completa desde la sala actual del cazador hasta la sala de destino donde está el jugador, incluyendo la salida final de ingreso a dicha sala.
- Q: ¿Qué ocurre si el cazador y el jugador se encuentran en salas vecinas pero la puerta directa que las comunica está cerrada? → A: El cazador no puede atacar porque no comparte sala con el jugador (P1 §2.8), ni puede abrir la puerta cerrada. En su turno evalúa si existe una ruta alternativa abierta que bordee el obstáculo; si existe y su costo total cumple d <= rango, avanza un paso por ella; si no existe o d > rango, espera con costo 100.
- Q: ¿Existe un límite de ocupación de actores por sala o colisión física que pueda bloquear el paso del cazador? → A: No. Siguiendo las reglas de P1, múltiples actores pueden coexistir simultáneamente en una misma sala. La presencia de otros actores o enemigos nunca bloquea una salida transitable ni impide la entrada o salida a una sala.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Costos de terreno en salidas y tiempos de tránsito (Priority: P1)

Como jugador o actor en la cripta, quiero que atravesar una salida tome un tiempo proporcional a su costo de tránsito y a mi velocidad para que la topografía y la dificultad del terreno influyan tácticamente en el ritmo y duración de los desplazamientos.

**Why this priority**: Es la base mecánica de la capacidad. Sin costos de tránsito diferenciados en las salidas, el cálculo de rutas más baratas y el comportamiento del nuevo enemigo carecerían de fundamento.

**Independent Test**: Puede probarse de manera aislada configurando salidas con costos explícitos e implícitos en una cripta preparada, comprobando la duración del movimiento para distintos actores y velocidades sin requerir la presencia de cazadores.

**Acceptance Scenarios**:

1. **Given** una salida que no declara costo explícito, **When** un actor la atraviesa con velocidad 100, **Then** la acción toma el costo base predeterminado de 100 y dura un intervalo de 100 unidades de tiempo virtual.
2. **Given** una salida con costo explícito declarado (por ejemplo, 250), **When** un actor la atraviesa en cualquiera de los dos sentidos posibles, **Then** el costo base de la acción es idéntico en ambas direcciones y el intervalo de movimiento equivale a `max(1, 250 * 100 // velocidad)`.
3. **Given** un actor con velocidad muy alta (por ejemplo, 300) y una salida de costo mínimo 1, **When** el actor atraviesa la salida, **Then** el intervalo resultante no se anula por redondeo y resulta en al menos 1 unidad de tiempo virtual (`max(1, 1 * 100 // 300) = 1`).
4. **Given** un actor que se encuentra atravesando una salida costosa, **When** su velocidad cambia en pleno trayecto debido a un efecto o modificación, **Then** el tiempo restante de su movimiento se reescala proporcionalmente según la regla de escalado temporal de P1 §2.3.
5. **Given** enemigos con comportamiento errante o rastreador, **When** deciden y ejecutan sus desplazamientos entre salas, **Then** conservan intacta su regla de selección de destino, pero el tiempo requerido para completar el paso refleja el costo de la salida atravesada.
6. **Given** cualquier actor que realiza acciones distintas a desplazarse (tales como atacar o esperar), **When** ejecuta dicha acción, **Then** el costo base y la duración de la acción no se ven modificados por los costos de las salidas circundantes.
7. **Given** una sala o salida donde coinciden varios actores, **When** un actor decide atravesar una salida abierta, **Then** la presencia de otros actores en la sala no bloquea su paso ni altera el cálculo del tiempo de tránsito.

---

### User Story 2 - Persecución estratégica del enemigo cazador (Priority: P1)

Como jugador, quiero enfrentarme a un enemigo cazador que evalúe la ruta de menor costo de tránsito hasta mi posición y me persiga activamente dentro de su rango para experimentar un reto táctico de evasión, gestión del tiempo y uso del entorno.

**Why this priority**: Introduce el nuevo tipo de adversario y aporta el valor jugable principal de la capacidad, interactuando directamente con el jugador y con los costos de terreno.

**Independent Test**: Puede probarse de manera aislada situando un cazador y al jugador en diversas configuraciones de salas con salidas abiertas de costos dispares, verificando el orden de decisiones (atacar, esperar o moverse un paso) y el consumo de tiempo correspondiente.

**Acceptance Scenarios**:

1. **Given** un cazador y el jugador compartiendo la misma sala en el turno del cazador, **When** el cazador actúa, **Then** ataca directamente al jugador siguiendo la regla de combate de P1 §2.8 sin calcular rutas ni desplazarse.
2. **Given** un cazador y el jugador en salas distintas donde existe una ruta abierta cuyo costo total mínimo `d` cumple `d <= rango` (incluyendo el caso límite donde `d == rango`), **When** el cazador actúa, **Then** avanza un paso por una ruta de costo mínimo `d`, y la acción consume el costo de la salida atravesada.
3. **Given** un cazador y el jugador en salas donde la ruta abierta de menor costo `d` supera el rango del cazador (`d > rango`), **When** el cazador actúa, **Then** permanece en su sala y espera, consumiendo un costo fijo de 100.
4. **Given** un cazador que no tiene ninguna ruta abierta hacia el jugador (por salidas bloqueadas por puertas cerradas o aislamiento topológico), **When** el cazador actúa, **Then** permanece en su sala y espera, consumiendo un costo fijo de 100.
5. **Given** una opción entre una ruta de pocas salas pero salidas muy costosas y otra ruta de mayor número de salas pero menor costo acumulado `d`, **When** el cazador decide su desplazamiento, **Then** elige la ruta de menor costo total acumulado `d` en lugar de la ruta de menor cantidad de salas.
6. **Given** un cazador y el jugador en salas vecinas comunicadas por una salida cuya puerta está cerrada, pero existiendo una ruta alterna abierta de costo total `d <= rango`, **When** el cazador actúa, **Then** no ataca (por no compartir sala) ni intenta forzar la puerta cerrada, y avanza un paso por la ruta alterna abierta de costo mínimo `d`.
7. **Given** un cazador y el jugador en salas vecinas con puerta cerrada y sin rutas alternas abiertas dentro de su rango (`d > rango` o sin ruta), **When** el cazador actúa, **Then** permanece en su sala y espera con costo 100.
8. **Given** una ruta evaluada entre el cazador y el jugador que atraviesa varias salidas, **When** se calcula el costo total `d`, **Then** la suma incluye de forma obligatoria el costo de la salida final que ingresa a la sala actual del jugador.

---

### User Story 3 - Determinismo, equivalencia observable y desempate estricto (Priority: P2)

Como árbitro y evaluador del juego, quiero que el cazador decida su movimiento de forma estrictamente determinista ante rutas equivalentes y reaccione dinámicamente a los cambios en el estado de las puertas y de los actores, asegurando reproducibilidad exacta de las partidas.

**Why this priority**: Garantiza que el juego sea reproducible, verificable mediante pruebas automáticas y coherente con el principio de cálculo desde cero e invariantes de desempate.

**Independent Test**: Puede probarse configurando salas equidistantes con salidas simétricas de igual costo y forzando cambios dinámicos de puertas entre turnos, comparando la sala elegida contra la vecina de menor identificador y contrastando contra un cálculo fresco desde cero.

**Acceptance Scenarios**:

1. **Given** un cazador en sala `u` donde dos o más salas vecinas `v` forman parte de rutas de costo mínimo idéntico `d` (cumpliendo `costo(u, v) + dist(v, jugador) == d`), **When** el cazador selecciona a cuál vecina avanzar, **Then** se desplaza invariablemente hacia la vecina `v` que posee el menor identificador de sala (`id`), independientemente de orientaciones espaciales o del orden de descubrimiento.
2. **Given** un cazador que se encuentra persiguiendo al jugador, **When** entre dos turnos una puerta de su trayectoria se cierra o se abre (o el jugador cambia de sala o velocidad), **Then** en su siguiente turno el cazador decide su acción con un resultado idéntico al que produciría un cálculo completo ejecutado desde cero en ese instante preciso.
3. **Given** una puerta abierta que tiene un evento de cierre automático programado en la agenda para un instante futuro posterior, **When** el cazador evalúa las salidas abiertas en su turno actual, **Then** considera dicha puerta como transitable y abierta, decidiendo su paso sin verse bloqueado anticipadamente por el cierre pendiente.
4. **Given** un cazador en una cripta con niebla de guerra y salas cuyo contenido aún no ha sido cargado o explorado por el jugador, **When** el cazador planifica su ruta hacia el jugador, **Then** toma su decisión conociendo la topografía completa de la cripta y el estado actual de todas las puertas, sin verse restringido por la niebla del jugador ni por la descarga diferida de las salas.
5. **Given** un cazador frente a una puerta cerrada en una ruta hacia el jugador, **When** evalúa sus opciones de tránsito, **Then** no intenta abrir la puerta cerrada y únicamente considera salidas abiertas en ese instante para calcular `d`.

---

### User Story 4 - Escalabilidad y fluidez del ciclo de eventos (Priority: P2)

Como jugador, quiero que el juego responda fluidamente y sin pausas perceptibles en la interfaz durante los ciclos de eventos, incluso cuando existan múltiples cazadores activos en la cripta.

**Why this priority**: Asegura que la complejidad de la persecución no degrade la experiencia de juego interactivo ni vulnere los límites temporales del motor.

**Independent Test**: Puede probarse midiendo el tiempo de resolución del ciclo de eventos del motor con decenas de cazadores simultáneos en criptas de referencia y comparando la sobrecarga computacional de cazadores de rango pequeño frente al tamaño global de la cripta.

**Acceptance Scenarios**:

1. **Given** una cripta con decenas de cazadores activos persiguiendo al jugador, **When** el motor resuelve el ciclo de eventos completo entre dos decisiones consecutivas del jugador, **Then** el tiempo total de procesamiento transcurrido en el ciclo es menor o igual a 20 ms.
2. **Given** un cazador con un rango de costo pequeño situado en una cripta de gran extensión, **When** toma su decisión de movimiento o espera, **Then** el esfuerzo de cálculo queda acotado a la región transitable dentro de su rango y no crece proporcionalmente con el número total de salas de la cripta.

---

### Edge Cases

- **Distancia exacta igual al rango (`d == rango`)**: El cazador se mueve; únicamente entra en estado de espera si `d > rango` o si no existe ninguna ruta transitable. El límite exacto pertenece al rango operativo de movimiento.
- **Inclusión de la salida final**: El costo `d` totaliza todas las salidas recorridas en la trayectoria hasta penetrar en la sala del jugador, sumando sin excepción la salida que ingresa a dicha sala.
- **Puerta con cierre automático pendiente**: Se evalúa únicamente el estado vigente en el instante exacto de la decisión. Si la puerta está abierta al momento del turno, es transitable; un cierre programado a futuro en la agenda de eventos no impide el cruce antes de que ocurra.
- **Cazador y jugador en salas vecinas con puerta cerrada**: No comparten sala, lo cual prohíbe el ataque cuerpo a cuerpo (P1 §2.8). Al no poder abrir puertas cerradas, el cazador busca un camino alternativo abierto dentro de su rango (`d <= rango`) o espera con costo 100 si no existe alternativa viable.
- **Concurrencia de múltiples actores por sala**: No existe límite de capacidad de actores por sala ni bloqueo físico de salidas por la presencia de otros actores o enemigos.
- **Velocidad de actor extrema con costo mínimo**: Al atravesar una salida de costo 1 con velocidad muy alta, la duración no es cero; la regla `max(1, ...)` asegura que la acción tarde al menos 1 unidad de tiempo virtual.
- **Ruta inexistente o cripta disconexa**: Si no hay ninguna secuencia de salidas abiertas que conecte al cazador con el jugador, el cazador espera con costo 100 sin generar errores ni bloqueos.
- **Ausencia de costo explícito en el diseño**: Si una salida no especifica un costo en los datos de la cripta, se asume un costo de 100 unidades en ambos sentidos de forma predeterminada.
- **Costos declarados no válidos**: Cualquier costo de salida debe ser un entero mayor o igual que 1; los valores menores a 1 son rechazados o ajustados al mínimo permitido de 1.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-CAZ-01**: Cada salida entre dos salas puede declarar un atributo `costo` (entero mayor o igual que 1). Si una salida no lo declara, su costo toma el valor predeterminado de 100. El costo de una salida es exactamente el mismo en ambos sentidos de circulación.
- **FR-CAZ-02**: La acción de atravesar una salida tiene como costo base el costo de tránsito propio de esa salida (en sustitución del valor fijo anterior de 100 de P1 §2.3). El intervalo de tiempo virtual consumido por el movimiento es `max(1, costo_salida * 100 // velocidad)`.
- **FR-CAZ-03**: La regla de cálculo del tiempo de tránsito por salidas aplica de manera universal a todos los actores del juego (jugador, cazadores, errantes y rastreadores). Los costos base y la duración de atacar, esperar y demás acciones permanecen inalterados. Los enemigos errantes y rastreadores conservan intacto su criterio de selección de movimiento, alterando únicamente el tiempo que tarda su desplazamiento según la salida elegida. La presencia de múltiples actores en una sala no limita su capacidad ni bloquea el tránsito por salidas abiertas para otros actores.
- **FR-CAZ-04**: El catálogo de comportamientos de enemigos admite el nuevo comportamiento `cazador`, el cual incluye un campo `rango` definido como un número entero expresado en unidades de costo de tránsito.
- **FR-CAZ-05**: En su turno de acción dentro de la agenda, el cazador evalúa y ejecuta estrictamente en este orden:
  1. Si comparte la misma sala con el jugador, ejecuta un ataque directo hacia él siguiendo las reglas de combate de P1 §2.8.
  2. Si no comparte sala con el jugador, determina el costo mínimo `d` para alcanzar la sala actual del jugador sumando los costos de las salidas que componen la ruta completa, incluyendo la salida que ingresa a la sala actual del jugador.
  3. Si no existe ninguna ruta abierta hacia el jugador, o si el costo mínimo `d` es estrictamente mayor que su rango (`d > rango`), permanece en su sala y realiza la acción de esperar (con costo base 100). Si `d <= rango` (incluyendo `d == rango`), no espera y procede al siguiente paso.
  4. Si existe ruta abierta y `d <= rango`, avanza un único paso desplazándose hacia una sala vecina a través de una ruta de costo mínimo `d`; el costo de esta acción equivale al costo de la salida atravesada.
- **FR-CAZ-06**: El cálculo del costo mínimo `d` debe considerar exclusivamente salidas que se encuentren efectivamente abiertas en el estado vigente del reloj virtual en ese instante preciso de la decisión. Un cierre automático programado para un instante futuro en la agenda no altera la condición de abierta hasta su efectiva ejecución.
- **FR-CAZ-07**: Si no hay ruta abierta o `d > rango`, el cazador espera con un costo de acción fijo de 100. El límite `d == rango` autoriza el movimiento y no produce espera.
- **FR-CAZ-08**: Si existe ruta transitable y `d <= rango`, el cazador se desplaza a una sala contigua a través de una salida abierta que inicie una trayectoria de costo mínimo `d`; la acción consume el costo asignado a esa salida.
- **FR-CAZ-09**: Ante empates entre múltiples salas vecinas `v` conectadas con la sala actual del cazador `u` que formen parte de rutas de costo total mínimo `d` (es decir, donde `costo(u, v) + dist(v, jugador) == d`), el cazador se mueve invariablemente a la vecina `v` que tenga el menor identificador (`id`), sin importar el método de cálculo o búsqueda empleado.
- **FR-CAZ-10**: El cazador posee conocimiento completo del esqueleto de la cripta (incluyendo todos los costos de salida) y del estado actual de apertura o cierre de todas las puertas. Su toma de decisiones no se ve limitada por la niebla de guerra del jugador, nunca abre puertas cerradas y no depende de si el contenido de una sala ha sido descargado o visitado previamente. Una puerta cerrada entre salas contiguas prohíbe el ataque cuerpo a cuerpo y el cruce directo, obligando a buscar una ruta alterna abierta de costo mínimo o a esperar si no existe dentro del rango.
- **FR-CAZ-11**: La decisión del cazador en cada turno debe ser observablemente equivalente e idéntica a la que produciría un cálculo realizado completamente desde cero en ese mismo instante, incluso si entre turnos se abren o cierren puertas, cambia la posición del jugador, mueren actores o se alteran las velocidades. Se autoriza la reutilización de cálculos previos únicamente si se garantiza que la decisión resultante nunca difiere de la evaluación desde cero.
- **FR-CAZ-12**: Si la velocidad de un actor que se encuentra en tránsito a través de una salida cambia antes de completar su movimiento, el tiempo restante para concluir la acción se reescala proporcionalmente según lo dispuesto en P1 §2.3.
- **FR-CAZ-13**: La interfaz visual del juego muestra con claridad los costos de tránsito de todas las salidas correspondientes a la sala en la que se encuentra el jugador y distingue visualmente a los enemigos cazadores de los demás tipos de enemigos.
- **FR-CAZ-14** (Rendimiento): La resolución completa del ciclo de eventos del motor entre dos turnos de decisión del jugador requiere como máximo 20 ms con decenas de cazadores activos. Para un cazador con rango de costo pequeño, el trabajo de cálculo de su decisión debe acotarse a la región dentro de su rango y no crecer en proporción al tamaño total de la cripta.
- **FR-CAZ-15** (Medición y evaluación comparativa): El modo `--bench` permite comparar de forma reproducible: el rendimiento de un cazador frente a decenas de cazadores concurrentes, el impacto de rangos de costo pequeños frente a rangos amplios, estrategias de cálculo compartido frente a individual, y recálculo total frente a reutilización de trayectorias, tanto en escenarios con puertas estables como en escenarios con puertas inestables.

### Key Entities

- **Salida**: Conexión bidireccional entre dos salas contiguas de la cripta. Posee un atributo de costo de tránsito entero (>= 1, predeterminado en 100) simétrico en ambos sentidos, y un estado de puerta (abierta o cerrada). No está sujeta a límites de flujo o bloqueo por acumulación de actores.
- **Cazador**: Enemigo dotado de posición actual en la cripta, velocidad de desplazamiento y un atributo de rango de persecución expresado en unidades de costo. Aplica una regla de persecución por ruta de menor costo hacia el jugador o combate directo si coinciden en la sala.
- **Sala**: Espacio transitable de la cripta identificado unívocamente por un id numérico/ordinal, que sirve de referencia posicional para actores y determina el criterio de desempate en la navegación. Admite múltiples actores simultáneos sin límite de capacidad.
- **Ruta de Costo Mínimo**: Secuencia ordenada de salidas transitables abiertas que conectan la sala del cazador con la sala actual del jugador, cuyo costo acumulado `d` es la suma de los costos de cada una de sus salidas (incluyendo la salida de entrada a la sala del jugador).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-CAZ-01**: El ciclo de eventos entre dos turnos del jugador no sobrepasa los 20 ms de tiempo de procesamiento en escenarios de prueba con decenas de cazadores activos simultáneamente.
- **SC-CAZ-02**: En cazadores con rango pequeño, el tiempo de cómputo de la decisión por turno se mantiene acotado a la región de salas alcanzables dentro de su rango, sin incrementar proporcionalmente al aumentar el número total de salas de la cripta.
- **SC-CAZ-03**: El 100% de las decisiones adoptadas por los cazadores en cada turno coinciden de forma verificable con el resultado teórico de un cálculo desde cero, satisfaciendo estrictamente el criterio de desempate por menor id de sala contigua y respondiendo coherentemente a modificaciones dinámicas del estado de las puertas y de la agenda de eventos.
- **SC-CAZ-04**: El cálculo del intervalo de desplazamiento de cualquier actor a través de una salida de costo arbitrario `c` y velocidad `v` resulta exactamente en `max(1, c * 100 // v)`, asegurando que nunca sea menor a 1 unidad de tiempo virtual.

## Assumptions

- **Fuente normativa contrastada2026-11-16**: `docs/Cripta Parte II.md`, §§3.1–3.2,5.1–5.2,6.1; reglas de costo, persecución, desempate, independencia de contenido y presupuestos coinciden con esta especificación.
- **Fuentes de referencia**: Guía de parte II (`docs/CRIPTA Parte II guía y división del trabajo.md`), enunciado general P1 (`docs/enunciado.md`) y principios de la constitución del proyecto (`.specify/memory/constitution.md`).
- **Aclaraciones ratificadas**: Las respuestas de la sesión 2026-11-09 formalizan que $d == \text{rango}$ habilita el movimiento; que el estado de puerta abierta es el efectivo al instante del turno sin anticipar eventos futuros de la agenda; que $d$ incluye la salida final hacia la sala del jugador; que salas vecinas con puerta cerrada prohíben el ataque forzando desvíos abiertos o espera; y que no rige límite de ocupación de actores por sala.
- **Combate y activación**: Se preservan las reglas de combate, cálculo de daño y resolución de ataque de P1 §2.8 cuando el cazador comparte sala con el jugador.
- **Ausencia de prescripción de implementación**: En cumplimiento estricto con las directrices de especificación y la constitución del proyecto, este documento describe el comportamiento observable y los requisitos funcionales del juego sin mencionar estructuras de datos, clases ni módulos concretos del software.

### Descripción de entrada conservada

Texto original de referencia utilizado como base para esta especificación:

Capacidad: terreno y cazador. Desde el punto de vista del juego, las salidas ahora tienen un costo de tránsito y aparece un enemigo que persigue al jugador por la ruta más barata.

Cada salida puede declarar un costo, entero mayor o igual que 1. Si no lo declara, vale 100. El costo es el mismo en ambos sentidos. Atravesar una salida es una acción cuyo costo base es el de esa salida (en lugar del 100 fijo de P1 §2.3). El intervalo es max(1, costo_salida * 100 // velocidad). Aplica a todos los actores. El costo de atacar, esperar y las demás acciones no cambia. Errantes y rastreadores solo cambian lo que tarda su movimiento.

Se agrega el comportamiento de enemigo «cazador», con un campo rango (entero, en unidades de costo). En su turno, en orden: (1) si comparte sala con el jugador, ataca (P1 §2.8); (2) si no, considera el costo mínimo d de llegar a la sala actual del jugador sumando el costo de cada salida recorrida, usando solo salidas abiertas en ese instante; (3) si no hay ruta, o si d > rango, espera (costo 100); (4) si hay, se mueve un paso por una ruta de costo d, y la acción cuesta lo que la salida que atraviesa.

Desempate: sea u la sala del cazador; entre las vecinas v tales que costo(u,v) + dist(v, jugador) = d, se mueve a la de menor id, sin importar cómo se calcule.

El cazador conoce el esqueleto completo (con costos) y el estado actual de todas las puertas. No le afecta la niebla de guerra del jugador, no abre puertas cerradas y su decisión nunca depende de si el contenido de una sala ya fue descargado.

Equivalencia observable: la decisión en cada turno debe ser idéntica a la que daría un cálculo desde cero en ese instante, aunque entre turnos se abran o cierren puertas, se mueva el jugador, mueran otros actores o cambien velocidades. Se pueden reutilizar cálculos anteriores solo si nunca cambia la decisión.

Rendimiento: el ciclo de eventos entre dos decisiones del jugador toma como máximo 20 ms con decenas de cazadores activos. La decisión de un cazador de rango pequeño no debe costar proporcionalmente al tamaño de la cripta, sino a la región dentro de su rango.

No mencionar estructuras de datos, clases ni módulos.
