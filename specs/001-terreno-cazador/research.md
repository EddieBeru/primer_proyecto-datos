# Phase 0: Research & Technical Decisions — Terreno y cazador (001)

Este documento consolida la investigación técnica, evaluación de alternativas y justificación de decisiones para la capacidad `001-terreno-cazador`, en cumplimiento estricto con la constitución del proyecto (`.specify/memory/constitution.md`) y las restricciones académicas de `docs/enunciado.md`.

---

## 1. Estructura de Cola de Prioridad: Montículo Propio vs. Lista Enlazada Ordenada

### Problema
Para determinar la ruta de menor costo de tránsito $d$ desde la sala del cazador hacia el jugador (o desde el jugador hacia los cazadores), se requiere un algoritmo de caminos mínimos (Dijkstra) que consulte y extraiga repetidamente el nodo alcanzable con menor costo acumulado. La estructura auxiliar debe operar bajo la restricción constitucional absoluta: **PROHIBIDO usar `heapq`, `deque`, `set` ni `dict` como estructuras evaluadas**.

### Alternativas Evaluadas

1. **Reutilizar la lista enlazada ordenada de la agenda de eventos (`Agenda` / DLL)**:
   - *Funcionamiento*: Mantener la frontera de exploración ordenada insertando cada vecino de forma lineal.
   - *Ventajas*: La estructura ya existe y está validada en la agenda de eventos (`src/controller2/agenda.py`).
   - *Desventajas*: En Dijkstra, se realizan $O(V)$ extracciones del mínimo (que son $O(1)$ al inicio de la lista) y hasta $O(E)$ inserciones/actualizaciones con costos arbitrarios. Cada inserción en una lista enlazada requiere un barrido lineal $O(V)$, resultando en una complejidad global de $O(V^2 + E \cdot V) = O(V^2)$. En criptas de $1\,000$ a $10\,000$ salas, una sola búsqueda requeriría millones de operaciones elementales, superando con creces el límite de 20 ms estipulado en `FR-CAZ-14`. Además, la agenda de eventos fue diseñada para cancelaciones arbitrarias O(1) basadas en secuencia y tipo, algo innecesario en Dijkstra donde se usa borrado perezoso con etiquetas.

2. **Montículo binario mínimo propio en arreglo dinámico (`MonticuloMinimo`)**:
   - *Funcionamiento*: Implementación propia en `src/estructuras/monticulo_minimo.py` mediante una lista Python utilizada exclusivamente como arreglo contiguo base indexado `0..n-1`. Las operaciones de flotar (*sift-up*) y hundir (*sift-down*) mantienen la propiedad de árbol binario casi completo.
   - *Ventajas*: 
     - Inserción en $O(\log V)$.
     - Extracción del mínimo en $O(\log V)$.
     - Complejidad total de Dijkstra: $O((V + E) \log V)$. Para una región de $1\,000$ salas y grado medio 4, requiere $\approx 5\,000 \times 10 = 50\,000$ operaciones (frente a $1\,000\,000$ con lista enlazada, una aceleración de más de $20\times$).
     - No utiliza `heapq` ni módulos externos.
     - Incluye desempate determinista por número de secuencia de inserción para garantizar estabilidad total.

### Decisión
**Implementar y emplear `MonticuloMinimo` propio** combinado con `TablaIndice` propia para las etiquetas de distancia. La lista enlazada de la agenda se **descarta** para la búsqueda de rutas por su ineficiencia asintótica cuadrática ($O(V^2)$), reservándola exclusivamente para la agenda cronológica donde las inserciones ocurren de forma natural en el extremo del tiempo virtual.

*Trazabilidad*: Cubre `FR-CAZ-05`, `FR-CAZ-06`, `FR-CAZ-14`.

---

## 2. Estrategia de Persecución: Cálculo Individual vs. Compartido

### Problema
En una cripta pueden coexistir decenas de cazadores persiguiendo simultáneamente al jugador. Se debe decidir si cada cazador ejecuta su propia búsqueda hacia el jugador o si se comparte un cálculo global, satisfaciendo al mismo tiempo:
- `FR-CAZ-14`: Un cazador con rango pequeño debe costar proporcionalmente a su región, no al tamaño global de la cripta.
- `FR-CAZ-11`: Equivalencia observable exacta con un cálculo desde cero en cada turno.
- `FR-CAZ-09`: Desempate determinista por menor `id` de vecina.

### Alternativas Evaluadas

1. **Cálculo Individual Acotado (Dijkstra desde el cazador hacia el jugador)**:
   - El algoritmo inicia en la sala del cazador $u$ y expande salas hasta alcanzar al jugador o agotar la frontera dentro de `rango`.
   - *Ventajas*: La búsqueda está acotada estrictamente por `rango`. Si el rango es 300 y el costo medio por salida es 100, la búsqueda explora a lo sumo 3 niveles de profundidad ($\approx 10\text{–}30$ salas), independientemente de que la cripta tenga $10\,000$ salas. Satisface directamente `FR-CAZ-14`.
   - *Desventajas*: Con $K$ cazadores activos en el mismo instante, se ejecutan $K$ búsquedas locales independientes.

2. **Cálculo Compartido Inverso (Dijkstra desde el jugador hacia toda la cripta)**:
   - Dado que los costos de las salidas son simétricos (`FR-CAZ-01`), la distancia mínima $dist(u, jugador) = dist(jugador, u)$.
   - Se ejecuta un único Dijkstra iniciando en la sala actual del jugador, calculando las distancias a todas las salas alcanzables.
   - Cada cazador $u$ consulta en $O(1)$ su distancia y la de sus vecinas $v$ para decidir su movimiento.
   - *Ventajas*: Con 50 cazadores en un mismo turno, se realiza un solo Dijkstra en vez de 50.
   - *Desventajas*: Explora toda la cripta desde el jugador, violando `FR-CAZ-14` si hay un solo cazador lejano con rango pequeño.

3. **Cálculo Compartido con Cota Superior Dinámica**:
   - Se ejecuta un Dijkstra desde el jugador, pero acotado a la cota máxima: $R_{max} = \max_{h \in \text{cazadores activos}}(rango_h)$.
   - Si no hay cazadores o solo hay 1 cazador con rango pequeño, $R_{max}$ acota la búsqueda exactamente a esa vecindad.
   - Si hay múltiples cazadores en el ciclo de eventos, un solo árbol de distancias desde el jugador resuelve a todos los cazadores cuyo $dist(jugador, u) \le rango_u$.

### Decisión
**Adoptar un diseño modular que soporte ambas estrategias y las evalúe en `--bench` (conforme a `FR-CAZ-15`)**:
- En el motor de juego (`controller2`): Se emplea **Dijkstra individual acotado por rango** cuando actúa un cazador individual en su turno de agenda, garantizando que el tiempo de cálculo sea estrictamente proporcional a la región alcanzable dentro de su `rango` (`FR-CAZ-14`).
- Para escenarios concurrentes con múltiples cazadores en el mismo ciclo, se provee el modo de **cálculo compartido desde el jugador** acotado por $\max(rango)$.
- Ambos métodos producen decisiones idénticas (`FR-CAZ-11`), cumpliendo con la regla de desempate por menor `id` de vecina (`FR-CAZ-09`).

*Trazabilidad*: Cubre `FR-CAZ-06`, `FR-CAZ-09`, `FR-CAZ-11`, `FR-CAZ-14`, `FR-CAZ-15`.

---

## 3. Reutilización de Rutas y Política de Invalidación Estricta

### Problema
Para optimizar el rendimiento, un cazador podría reutilizar una ruta calculada en un turno anterior. Sin embargo, `FR-CAZ-11` exige de forma terminante: *«la decisión en cada turno debe ser idéntica a la que daría un cálculo desde cero en ese instante, aunque entre turnos se abran o cierren puertas, se mueva el jugador, mueran otros actores o cambien velocidades»*. Se requiere definir con precisión matemática cuándo una ruta es válida y cuándo queda invalidada.

### Análisis Causal de Factores de Invalidación

1. **Movimiento del Jugador**:
   - Si el jugador se desplaza a otra sala, el destino del camino ha cambiado. La ruta anterior apuntaba a una sala que ya no contiene al jugador.
   - $\implies$ **INVALIDACIÓN TOTAL INMEDIATA**.

2. **Apertura o Cierre de Puertas**:
   - Si una puerta se cierra en la ruta del cazador: la ruta queda bloqueada y no se puede transitar.
   - Si una puerta se abre en cualquier parte del entorno dentro del rango: puede haber aparecido un atajo de menor costo total que la ruta previamente calculada.
   - Por tanto, cualquier cambio en el estado de una puerta (abrirse o cerrarse, sea manual o por cierre automático de la agenda) altera el grafo transitable.
   - $\implies$ **INVALIDACIÓN TOTAL INMEDIATA**. Se mantiene un contador entero de versión de puertas (`puertas_version`) en `EstadoPartida` que se incrementa en cada mutación de puerta.

3. **Muerte de Otros Actores o Modificación de Velocidades**:
   - En el modelo de CRIPTA, los actores no poseen colisión física ni bloquean el tránsito por salidas (Aclaración 5 / `FR-CAZ-03`).
   - La velocidad de un actor altera el tiempo de tránsito virtual (`intervalo`), pero **no altera el costo de tránsito intrínseco de la salida**.
   - $\implies$ **NO INVALIDA LA RUTA**. La ruta y la decisión de movimiento son completamente independientes de la vida o velocidad de otros actores.

4. **Avance del Cazador en Entorno Inalterado**:
   - Si el cazador dio un paso hacia la vecina $v$, y entre ese instante y su siguiente turno:
     a) El jugador no cambió de sala,
     b) Ninguna puerta cambió de estado (`puertas_version` no cambió),
   - Por el principio de optimalidad de Bellman, la sub-ruta restante sigue siendo la ruta de costo mínimo hacia el jugador, con costo $d' = d - costo(u, v) \le rango$.
   - $\implies$ **REUTILIZACIÓN SEGURA Y EQUIVALENTE**. El cazador puede tomar el siguiente paso de la ruta en caché sin recalcular.

### Decisión
Cada ruta en caché se almacena asociada a una clave de validación:
```text
ClaveValidez = (puertas_version: int, sala_jugador: int, sala_actual_cazador: int)
```
Si en el turno del cazador la clave coincide exactamente con el estado actual del juego, se reutiliza el siguiente paso de la ruta. Si la clave difiere o la ruta está vacía, se realiza un cálculo fresco desde cero. El modo `--bench` compara el rendimiento de **recálculo siempre** vs. **reutilización con invalidación estricta** bajo puertas estables e inestables (`FR-CAZ-15`).

*Trazabilidad*: Cubre `FR-CAZ-10`, `FR-CAZ-11`, `FR-CAZ-15`.

---

## 4. Determinismo y Desempate Estricto por Menor ID (FR-CAZ-09)

### Problema
Cuando existen múltiples rutas de costo mínimo idéntico $d$, el cazador debe seleccionar inequívocamente a cuál sala vecina avanzar:
*«entre las vecinas v tales que costo(u,v) + dist(v, jugador) = d, se mueve a la de menor id, sin importar cómo se calcule»*.

### Alternativas Evaluadas

1. **Desempate en la inserción/extracción de Dijkstra**:
   - Modelar las etiquetas del montículo como tuplas `(costo_acumulado, primer_vecino_id, nodo)`.
   - Al relajar desde el cazador $u$, cada vecina $v$ fija `primer_vecino_id = v`.
   - *Ventajas*: La extracción del destino entrega directamente la tupla óptima con el menor `primer_vecino_id`.
   - *Desventajas*: El orden de relajación de aristas o arcos paralelos podría introducir sesgos sutiles si no se cuida rigurosamente la estabilidad de la comparación.

2. **Evaluación Explícita sobre las Vecinas de la Sala Actual**:
   - Sea $u$ la sala del cazador y $J$ la sala del jugador.
   - Para cada vecina $v$ conectada con $u$ mediante una salida abierta:
     1. Obtener $c(u, v) = salida.costo$.
     2. Calcular o consultar $dist(v, J)$.
     3. El costo total a través de $v$ es $d_v = c(u, v) + dist(v, J)$.
   - Encontrar el mínimo global $d = \min_{v \in vecinas\_abiertas(u)} d_v$.
   - Si no hay camino o $d > rango$, esperar con costo 100.
   - Si $d \le rango$, filtrar el conjunto de candidatas óptimas:
     $$V^* = \{ v \in vecinas\_abiertas(u) \mid d_v = d \}$$
   - Seleccionar la vecina destino como $\min(V^*)$ según el valor numérico del identificador entero `id`.

### Decisión
**Implementar la Evaluación Explícita sobre las Vecinas de la Sala Actual**. 
Esta técnica desacopla la decisión final de las peculiaridades internas del algoritmo de búsqueda o del orden de descubrimiento de grafos, garantizando matemáticamente el cumplimiento estricto de `FR-CAZ-09` y `FR-CAZ-11`.

*Trazabilidad*: Cubre `FR-CAZ-05`, `FR-CAZ-08`, `FR-CAZ-09`, `FR-CAZ-11`.

---

## 5. Poda por Rango en Montículo para Escalabilidad Regional (FR-CAZ-14)

### Problema
`FR-CAZ-14` y `SC-CAZ-02` exigen: *«La decisión de un cazador de rango pequeño no debe costar proporcionalmente al tamaño de la cripta, sino a la región dentro de su rango»*.

### Diseño del Algoritmo Acotado
1. Al explorar desde la sala $u$ con rango $R$:
   - Toda arista saliente hacia un nodo $w$ con costo tentativo acumulado $g(w) = g(actual) + costo\_salida$ se descarta si $g(w) > R$. No se inserta en el montículo.
   - Si el montículo se vacía antes de alcanzar la sala del jugador, se concluye formalmente que $dist(u, jugador) > R$ (o no hay ruta abierta).
   - El número de salas visitadas y aristas relajadas queda acotado superiormente por el subgrafo inducido por la bola $B(u, R) = \{ w \mid dist(u, w) \le R \}$.
2. En criptas sintéticas de $10\,000$ salas, una consulta con $R=300$ explora un promedio de $\le 25$ salas y tarda menos de 0.2 ms, independientemente del volumen total del mapa.

*Trazabilidad*: Cubre `FR-CAZ-14`, `SC-CAZ-02`.

---

## 6. Extensiones de Modelo y Contratos de API

### Salidas de Salas (`Exit` y `SalidaViva`)
- Se incorpora el atributo `costo: int = 100` (mayor o igual a 1).
- En serialización/deserialización (`from_dict`):
  ```python
  costo = int(data.get("costo", 100))
  if costo < 1:
      raise ValueError("El costo de salida debe ser entero >= 1")
  ```
- Coherencia física: Las salidas recíprocas entre dos salas contiguas comparten el mismo costo en ambos sentidos (`FR-CAZ-01`).

### Catálogo de Enemigos (`Enemy` y `EnemigoInstancia`)
- Se añade el valor `"cazador"` a la enumeración de comportamientos válidos:
  `Literal["guardián", "errante", "rastreador", "cazador"]`.
- Se incorpora el atributo `rango: Optional[int] = None`.
- Validación: Para enemigos con comportamiento `"cazador"`, `rango` es un entero obligatorio $\ge 1$. Para otros comportamientos, `rango` puede ser `None`.

### Cálculo Temporal Universal
- Atravesar una salida tiene costo base igual al costo de la salida:
  $$\text{intervalo} = \max(1, \text{costo\_salida} \times 100 // \text{velocidad})$$
- Aplica universalmente a jugador, cazadores, errantes y rastreadores (`FR-CAZ-02`, `FR-CAZ-03`).
- Las acciones de atacar, esperar, abrir puertas, usar objetos y recoger/soltar conservan sus costos fijos (100, 50, 25).
- Reescalado de velocidad (`FR-CAZ-12`): Se mantiene la función `reescalar` de `src/controller2/reloj.py` que preserva el progreso virtual remanente.

*Trazabilidad*: Cubre `FR-CAZ-01`, `FR-CAZ-02`, `FR-CAZ-03`, `FR-CAZ-04`, `FR-CAZ-12`.

---

## 7. Plan de Medición con `--bench` (FR-CAZ-15)

El comando `python -m src.main --bench` incorporará una suite de pruebas de rendimiento reproducible para `001-terreno-cazador`:

1. **Un cazador vs. Muchos**: Comparar el tiempo del ciclo de eventos con 1 cazador activo vs. 50 cazadores activos en una cripta de $1\,000$ salas. Meta: ciclo completo $\le 20\text{ ms}$ (`FR-CAZ-14`, `SC-CAZ-01`).
2. **Rango pequeño vs. Rango grande**: Comparar tiempos con $R=200$ vs. $R=5\,000$ en criptas de 100, $1\,000$ y $10\,000$ salas para verificar que el costo de $R$ pequeño permanece constante frente al crecimiento de la cripta (`SC-CAZ-02`).
3. **Cálculo compartido vs. Cálculo individual**: Medir 25 cazadores simultáneos resolviendo mediante búsquedas acotadas individuales vs. Dijkstra compartido desde el jugador.
4. **Reutilización vs. Recálculo siempre**: Medir una partida de 200 turnos con puertas estables (demostrando reducción de tiempo por aciertos de caché) y con puertas inestables (midiendo el overhead de comprobación de versión y recálculo).
5. **Montículo propio (`MonticuloMinimo`) vs. Lista enlazada ordenada**: Medición comparativa que justifique empíricamente en `DECISIONES.md` el rechazo de la lista enlazada para grafos medianos y grandes.

*Trazabilidad*: Cubre `FR-CAZ-14`, `FR-CAZ-15`, `SC-CAZ-01`, `SC-CAZ-02`.
