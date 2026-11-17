# Feature Specification: Verificación de resolubilidad

**Feature Branch**: sin rama dedicada; directorio independiente de la rama Git actual (`main`).

**Created**: 2026-11-16

**Status**: Draft — validada para planificación.

**Input**: solicitud del usuario mediante `$speckit-specify`: determinar antes de jugar si la cripta puede ganarse; entregar un orden determinista de llaves o explicar bloqueos y ciclos; permitir `--forzar` y `--verificar <cripta>`; respetar 200 ms, crecimiento aproximadamente lineal y `presupuesto_solicitudes`, sin prescribir implementación.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Conocer la posibilidad de ganar antes de jugar (Priority: P1)

Como jugador, quiero que el programa compruebe si puedo ganar antes de iniciar una partida y me muestre el resultado para evitar jugar una cripta imposible sin saberlo.

**Why this priority**: establece la condición de victoria comprobada y protege el inicio de la partida.

**Independent Test**: intentar iniciar criptas con solución conocida y sin solución, y comparar el reporte y la autorización de inicio.

**Acceptance Scenarios**:

1. **Given** una llave A accesible desde el inicio, una llave B tras una puerta que requiere A y `llave_salida` tras una puerta que requiere B, **When** se inicia la cripta y existe un acceso a `sala_salida` por una puerta que requiere `llave_salida`, **Then** se informa que es resoluble, el orden sitúa A antes de B y B antes de `llave_salida`, y la partida inicia mostrando el reporte.
2. **Given** `llave_salida` obtenible pero ningún acceso posible a `sala_salida` por una puerta que la requiera, **When** se intenta iniciar sin `--forzar`, **Then** se informa que no es resoluble, se explica la condición de salida incumplida y la partida no inicia.
3. **Given** una cripta no resoluble, **When** se solicita iniciar con `--forzar`, **Then** se muestra el reporte de imposibilidad y la partida inicia sin alterar el diagnóstico.
4. **Given** una llave opcional inaccesible y una ruta válida de victoria, **When** se verifica, **Then** la cripta es resoluble y el orden contiene únicamente llaves obtenibles, sin exigir obtener la llave opcional.

---

### User Story 2 - Entender los bloqueos y los ciclos (Priority: P1)

Como jugador o autor de una cripta, quiero identificar las llaves inaccesibles, las puertas que detienen el avance y las dependencias circulares para entender por qué no se puede ganar.

**Why this priority**: un resultado negativo solo es útil si permite localizar las causas concretas.

**Independent Test**: verificar criptas preparadas con un bloqueo directo, una cadena circular, regiones desconectadas y rutas alternativas; cotejar identificadores, ubicaciones y ciclos con su descripción.

**Acceptance Scenarios**:

1. **Given** `llave_salida` detrás de la única puerta que ella misma abre, **When** se verifica, **Then** el reporte identifica la llave como no obtenible, la puerta de frontera con su llave requerida y ubicación, y el ciclo concreto `llave_salida → llave_salida`, incluyendo la puerta que lo causa.
2. **Given** A solo obtenible tras una puerta que exige B y B solo obtenible tras una puerta que exige A, sin alternativa accesible, **When** se verifica una cripta cuya victoria depende de esas llaves, **Then** el reporte identifica un ciclo cerrado A → B → A, o su rotación equivalente, con las puertas y ubicaciones que justifican cada dependencia.
3. **Given** una aparente dependencia circular pero una ruta abierta alternativa para obtener una de sus llaves y completar la victoria, **When** se verifica, **Then** se declara resoluble y no se presenta esa dependencia como bloqueo inevitable.
4. **Given** una cripta no resoluble con llaves en una región desconectada y sin ciclos, **When** se verifica, **Then** se enumeran las llaves inaccesibles y sus ubicaciones, se informa la frontera existente o que está vacía, y no se inventa un ciclo.
5. **Given** varias llaves simultáneamente obtenibles o varios ciclos bloqueantes, **When** se repite la verificación con los mismos datos, **Then** el orden o el reporte completo, incluida la selección y presentación del ciclo, es idéntico.

---

### User Story 3 - Verificar sin abrir la interfaz (Priority: P2)

Como autor de criptas, quiero ejecutar solo la verificación para consultar el resultado sin iniciar una partida ni abrir la interfaz.

**Why this priority**: permite revisar criptas de forma independiente al juego.

**Independent Test**: ejecutar `--verificar <cripta>` para una cripta resoluble y otra no resoluble; comprobar el reporte y la ausencia de partida y de creación de la vista.

**Acceptance Scenarios**:

1. **Given** una cripta resoluble, **When** se ejecuta `--verificar <cripta>`, **Then** se informa el resultado y el orden de llaves, sin instanciar la vista ni iniciar una partida.
2. **Given** una cripta no resoluble, **When** se ejecuta `--verificar <cripta>`, **Then** se presenta el diagnóstico completo sin instanciar la vista ni iniciar una partida.
3. **Given** `--verificar <cripta>` junto con `--forzar`, **When** se ejecuta, **Then** se mantiene el modo de solo verificación: no inicia una partida.

### Edge Cases

- Una llave que suelta un enemigo errante cuenta en la sala donde ese enemigo inicia, independientemente de movimientos posteriores; todo enemigo se considera derrotable.
- Trampas y cierres automáticos no impiden una solución; una misma llave permite reabrir y atravesar varias puertas sin consumirse.
- Las llaves presentes en la sala inicial son obtenibles sin una llave previa; las salidas abiertas pueden atravesarse sin poseer su llave declarada.
- Una puerta cerrada que exige una llave inaccesible sigue bloqueada; una llave requerida sin ubicación declarada se señala como no obtenible y con ubicación no declarada.
- Una puerta entre salas ya alcanzables no pertenece a la frontera bloqueada; tampoco una puerta cerrada cuya llave ya se obtuvo. Se respeta el sentido de paso declarado de cada salida.
- Llegar a `sala_salida` por otro acceso, o tener `llave_salida` sin poder atravesar hacia ella una puerta que la exige, no satisface por sí solo la condición de victoria.
- Si no puede obtenerse la información necesaria por error del servicio o presupuesto agotado, se informa que la verificación no pudo completarse, sin confundirlo con una demostración de imposibilidad.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El programa DEBE verificar la resolubilidad antes de iniciar una nueva partida usando el esqueleto y la ubicación de las llaves de la cripta seleccionada.
- **FR-002**: La verificación DEBE partir de la sala inicial y considerar atravesables las salidas abiertas y las cerradas cuya llave ya se obtuvo. Las llaves no se consumen, todo enemigo se considera derrotable y las llaves que suelta un enemigo se consideran obtenibles en su sala de inicio. Trampas y cierres automáticos no bloquean el avance porque una puerta puede reabrirse con la misma llave.
- **FR-003**: El resultado DEBE ser resoluble si y solo si, bajo esos supuestos, es posible obtener `llave_salida` y llegar a `sala_salida` atravesando hacia ella una puerta que requiere esa llave. No se exige obtener llaves opcionales inaccesibles.
- **FR-004**: Para una cripta resoluble, el resultado DEBE incluir cada llave obtenible una sola vez, en un orden realizable desde el inicio: las llaves necesarias para alcanzar cada llave por la ruta que justifica su obtención deben aparecer antes. Las rutas alternativas no convierten todas sus llaves en requisitos simultáneos.
- **FR-005**: Con los mismos datos de entrada, dos ejecuciones DEBEN producir el mismo resultado, orden de llaves y diagnóstico; se permite cualquier orden válido que cumpla esta reproducibilidad.
- **FR-006**: Para una cripta no resoluble, el reporte DEBE enumerar todas las llaves no obtenibles y todas las puertas de la frontera bloqueada con su llave requerida. La frontera se determina una vez agotadas las posibilidades de avance y comprende las puertas cerradas que impiden pasar desde la región alcanzable a una no alcanzable.
- **FR-007**: El reporte negativo DEBE indicar la ubicación de cada llave no obtenible y de cada llave requerida por las puertas de frontera, identificando su sala y, si corresponde, el enemigo que la suelta. Si no hay ubicación declarada, DEBE decirlo expresamente.
- **FR-008**: Si una llave no obtenible está detrás de puertas que solo ella permite abrir, directamente o mediante una cadena de llaves, el reporte DEBE señalar al menos un ciclo bloqueante concreto de forma determinista. DEBE mostrar la secuencia cerrada de llaves y las puertas y ubicaciones que justifican sus dependencias, sin atribuir un bloqueo inevitable a una dependencia evitable por otra ruta.
- **FR-009**: El reporte negativo DEBE indicar qué condición de victoria no puede cumplirse, incluso cuando no hay frontera bloqueada o no existe ciclo. Las listas vacías DEBEN presentarse como tales, sin omitir silenciosamente categorías del diagnóstico.
- **FR-010**: Sin `--forzar`, una cripta no resoluble NO DEBE iniciar una partida y DEBE mostrar el reporte. Con `--forzar`, DEBE mostrar el mismo diagnóstico y permitir el inicio.
- **FR-011**: `--verificar <cripta>` DEBE ejecutar exclusivamente la verificación y mostrar su resultado sin instanciar la vista ni iniciar una partida, incluso si también se proporciona `--forzar`.
- **FR-012**: La interfaz DEBE mostrar el reporte al intentar iniciar una partida, tanto si se permite como si se bloquea el inicio; el contenido DEBE ser coherente con el resultado del modo de solo verificación.
- **FR-013**: Las ubicaciones de llaves DEBEN obtenerse de la consulta de ubicación de llaves del servicio. Las solicitudes de esa consulta DEBEN contabilizarse dentro de `presupuesto_solicitudes`, sin un presupuesto independiente para la verificación. Las lecturas locales no consumen solicitudes de red.
- **FR-014**: El costo total DEBE crecer aproximadamente de forma lineal con la cantidad de salas, salidas y llaves. NO DEBE repetirse un recorrido completo por cada llave obtenida. El orden y el reporte, incluido el diagnóstico de ciclos, DEBEN derivarse del mismo recorrido, sin recorridos adicionales por llave.
- **FR-015**: La verificación completa, incluida la elaboración del resultado o diagnóstico, DEBE tardar como máximo 200 ms en la cripta publicada más grande, bajo las condiciones de medición de SC-004.
- **FR-016**: Si falta información necesaria por error de consulta o presupuesto agotado, el programa DEBE informar que no pudo completar la verificación y su causa, sin afirmar que la cripta es resoluble o no resoluble. `--forzar` autoriza omitir el bloqueo por imposibilidad demostrada; no autoriza omitir errores de carga.

### Key Entities

- **Cripta**: salas y salidas declaradas, sala inicial, `sala_salida`, `llave_salida` y `presupuesto_solicitudes`.
- **Llave y ubicación**: identificador, sala donde puede obtenerse y enemigo que la suelta cuando corresponde.
- **Región alcanzable**: salas a las que puede llegarse desde el inicio tras aprovechar todas las llaves obtenibles bajo los supuestos.
- **Puerta de frontera bloqueada**: puerta cerrada que impide salir de la región alcanzable hacia una sala no alcanzable, con sus extremos y llave requerida.
- **Resultado de verificación**: resoluble con orden de llaves, o no resoluble con condiciones de victoria incumplidas, llaves inaccesibles, frontera, ubicaciones y ciclo cuando existe.
- **Ciclo bloqueante**: secuencia cerrada de dependencias entre llaves inaccesibles, justificada por puertas y ubicaciones concretas.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100 % de los escenarios de aceptación y casos límite con información completa produce el resultado esperado; los casos de victoria y bloqueo distinguen correctamente obtener la llave de poder entrar por la puerta requerida.
- **SC-002**: En 100 verificaciones consecutivas de cada cripta de prueba con los mismos datos, el resultado completo es idéntico, incluidos orden, listas y ciclo elegido.
- **SC-003**: En todos los casos negativos de prueba, el reporte coincide con la relación esperada de llaves inaccesibles, puertas de frontera y ubicaciones; cada ciclo señalado puede comprobarse siguiendo sus puertas y llaves identificadas.
- **SC-004**: Con los datos necesarios ya disponibles y excluyendo espera de red y presentación visual, cada una de 100 verificaciones de la cripta publicada más grande termina en ≤ 200 ms, incluyendo orden y diagnóstico. Se registra versión, tamaño, equipo y tiempos; si esa cripta no está disponible, la aceptación de este criterio queda pendiente, sin sustituirla por una carga sintética.
- **SC-005**: En cargas reproducibles de tamaño creciente, incluidas cadenas largas de llaves y bloqueos circulares, el trabajo total permanece acotado por un factor constante de la suma de salas, salidas y llaves. La validación demuestra que obtener más llaves no multiplica los recorridos completos ni añade recorridos por llave para elaborar el reporte.
- **SC-006**: En todos los intentos de inicio de prueba, una cripta imposible se bloquea sin `--forzar` y se permite con él mostrando el reporte. Todos los casos de `--verificar` terminan sin partida y sin instanciar la vista.
- **SC-007**: El 100 % de las solicitudes de red usadas para consultar ubicaciones figura en el consumo de `presupuesto_solicitudes`; ninguna verificación excede ese límite. Los errores de información se distinguen de un diagnóstico negativo.

## Assumptions

- La solicitud actual del usuario define el alcance funcional de esta especificación. Se conserva [003-resolubilidad](../003-resolubilidad/spec.md) como antecedente; esta invocación crea un único directorio nuevo y lo establece como función activa, sin modificar el antecedente ni sus artefactos dependientes.
- Se aplican [la constitución](../../.specify/memory/constitution.md), [el enunciado, especialmente §2.12 y §5.1](../../docs/enunciado.md) y [los contratos vigentes y sus enmiendas](../../CONTRATOS.md). Esta especificación no atribuye el alcance nuevo a un enunciado oficial de parte II no proporcionado ni modifica contratos aprobados.
- La condición de victoria es la solicitada para esta verificación, bajo sus supuestos; no garantiza supervivencia, estrategia de combate ni resultado de una partida real.
- El orden incluye todas las llaves obtenibles, aunque la victoria pueda lograrse antes. La obtención se justifica por una ruta válida con las llaves anteriores; no se exige un orden numérico ni alfabético.
- Si existen varios ciclos bloqueantes, basta informar al menos uno de ellos, siempre el mismo para la misma entrada. Las llaves inaccesibles y las puertas de frontera sí se enumeran por completo.
- El análisis usa las salidas con los sentidos declarados, sin inventar conexiones inversas. Una llave puede abrir varias puertas.
- El objetivo de 200 ms se refiere al cálculo con los datos disponibles, sin espera de red ni presentación visual. Esta condición permite medir el trabajo propio del programa; las solicitudes siguen sujetas al presupuesto.
- Se depende de disponer del esqueleto y de la consulta de ubicación de llaves para la misma cripta y versión. Un fallo de obtención de datos impide emitir un veredicto y se informa como error de verificación.
- No se añaden requisitos de persistencia del reporte, cambios de guardado ni banderas adicionales. La planificación definirá la validación reproducible y cualquier propuesta de contrato necesaria.
