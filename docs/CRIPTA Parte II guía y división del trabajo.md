# CRIPTA Parte II: guía y división del trabajo

Resumen del enunciado de la segunda parte y propuesta para repartir la carga entre 2 personas.

## La idea general

La parte 2 es la misma Cripta de la parte 1, más cuatro capacidades nuevas y un proceso de trabajo nuevo. Lo que confunde es que el enunciado mezcla reglas del juego, estructuras de datos y metodología en el mismo documento.

Para cada capacidad se sigue siempre el mismo ciclo:

**especificar (spec-kit) → planear → tareas → código → pruebas → medir con `--bench` → documentar en DECISIONES.md**

Lo que se evalúa no es solo que funcione. También cuenta que escojan una estructura, la justifiquen con mediciones y que cada regla se pueda rastrear desde la especificación hasta una prueba.

## Las 4 capacidades

### 1. Terreno y cazador (§3.1, 3.2, 5.1, 5.2)

- Las salidas ahora tienen `costo`, que por defecto es 100. Moverse tarda según ese costo.
- Hay un enemigo nuevo, el cazador. En cada turno calcula la ruta más barata hacia el jugador, o sea **Dijkstra**. Si la ruta cuesta más que su `rango` o no existe, espera.
- Si hay empate, va a la vecina de menor id.
- El reto real es el rendimiento. Con decenas de cazadores y puertas que se abren y cierran, hay que decidir si cada cazador calcula por su cuenta o si comparten un cálculo, y cuándo se puede reutilizar una ruta vieja sin cambiar la decisión.
- Como `heapq` está prohibido, necesitan su propio montículo o cola de prioridad. Ya acordaron una cola de prioridad con listas enlazadas para la agenda. Evalúen si les sirve aquí o si es muy lenta para Dijkstra.

### 2. Niebla de guerra e «ir a» (§3.3, 3.4, 5.3)

- El jugador solo conoce lo que exploró. Cada sala es explorada, avistada o desconocida, y el mapa recuerda las puertas como estaban cuando las vio por última vez.
- La antorcha ahora sirve para explorar las salas vecinas sin activar enemigos ni trampas.
- `ir a <sala>` es un Dijkstra sobre el mapa conocido que ejecuta pasos normales uno por uno, y se detiene en ciertas condiciones (enemigos, daño, ruta bloqueada).
- Todo esto tiene que poder revertirse con el pergamino.

### 3. Resolubilidad (§3.5, 5.4)

- Antes de jugar, el programa decide si la cripta se puede ganar, usando el esqueleto y la ubicación de las llaves, que viene del endpoint nuevo `/llaves`.
- Si no se puede, reporta qué llaves no se pueden obtener, qué puertas bloquean y si hay un ciclo (la llave está detrás de la puerta que ella misma abre).
- Se exige un solo recorrido incremental, no repetir el recorrido por cada llave.

### 4. Línea de tiempo (§3.6, 5.5)

- Con `historia <t>` o `historia #k` se consulta el estado en cualquier momento pasado sin modificar nada.
- No se puede guardar una copia del estado en cada acción. Solo se permite un punto de control cada K acciones, más un registro de los cambios.
- Hay que medir memoria y tiempo para al menos 3 valores de K y justificar el valor por defecto.

## Lo transversal

- spec-kit: constitución, un `spec.md`, `plan.md` y `tasks.md` por capacidad, trazabilidad con IDs de requisito (FR-012) y bitácora de prompts.
- Cambios al API: `costo` en las salidas, `cazador` y `rango` en el catálogo, y el endpoint `/llaves`.
- §5.6: repetir las mediciones de la parte 1 (agenda e historial de retroceso) con la carga nueva.
- Formato de guardado nuevo, que tiene que detectar archivos viejos.
- `--bench` con todas las comparaciones que pide §6.3.

## Cómo dividirlo entre 2

Propuesta: separar por afinidad técnica.

| Persona A (grafos) | Persona B (estado e historia) |
| --- | --- |
| Terreno y cazador, con invalidación de rutas | Niebla de guerra e «ir a» |
| Resolubilidad | Línea de tiempo y puntos de control |
|  | Persistencia nueva y revisión §5.6 |

Los motivos:

- **A** concentra los algoritmos de grafos sobre el esqueleto. Terreno y resolubilidad comparten el modelo de datos del esqueleto con costos y llaves.
- **B** concentra lo que tiene que registrarse e invertirse (mapa conocido, pergamino, historia). Esas tres cosas son el mismo problema: guardar cambios de forma barata y poder deshacerlos. Si lo diseña una sola persona, queda coherente.
- Por peso en la nota, A tiene 35% y B tiene 25%. Para equilibrar, B se lleva la persistencia y §5.6, que son trabajo pesado en mediciones.

## Puntos de contacto

1. **Dijkstra lo usan los dos.** A lo escribe primero, y B decide si reutiliza esa búsqueda para «ir a» o la separa (§5.3 pide justificarlo).
2. **Pónganse de acuerdo al inicio** en el formato de los cambios de estado, porque la niebla, el pergamino y la historia dependen de él.
3. **Hagan juntos lo común:** instalar spec-kit, la constitución, el README, y revisar cada `plan.md` del otro con `/speckit.analyze`. Cualquiera de los dos puede ser interrogado sobre cualquier especificación en la defensa.
4. **Detecten `heapq` a tiempo.** Si el agente propone `heapq`, `deque` o `set` en un plan, hay que corregirlo en la fase de plan.

## Orden sugerido

Quedan 2 semanas hasta el 18 de noviembre. El historial de Git debe mostrar cada especificación confirmada antes de su código, así que:

1. Días 1-2: instalar spec-kit, escribir la constitución y las 4 especificaciones (`/speckit.specify` y `/clarify`).
2. Después: cada uno hace plan, tareas y código de lo suyo.
3. Al final: bench, DECISIONES.md y pruebas de aceptación para el Apéndice B.

## Especificaciones para `/speckit.specify`

Cada bloque trae: (a) el texto para pegar en `/speckit.specify`, (b) los requisitos con ID, (c) los escenarios de aceptación del Apéndice B y (d) preguntas para `/speckit.clarify`.

**Antes de empezar**

- Pongan los dos enunciados (P1 y P2) como Markdown dentro del repo, por ejemplo en `docs/`. El agente no lee el PDF, y estas especificaciones citan reglas de P1 (§2.3, §2.4, §2.7, §2.8, §2.11, §4.10).
- Una especificación no nombra estructuras de datos, clases ni módulos (§2.4). Por eso aquí no aparecen nombres de algoritmos; eso va en `plan.md`.
- Los IDs llevan prefijo por especificación para que no choquen en la trazabilidad: `FR-CAZ`, `FR-NIE`, `FR-RES`, `FR-LIN`.
- Cada invocación con texto propio se registra en `PROMPTS_LLM.md`.
- Carpetas sugeridas: `001-terreno-cazador`, `002-niebla-ir-a`, `003-resolubilidad`, `004-linea-de-tiempo`.

### Especificación 001: terreno y cazador

**Prompt para `/speckit.specify`**

```
Capacidad: terreno y cazador. Desde el punto de vista del juego, las salidas ahora tienen un costo de tránsito y aparece un enemigo que persigue al jugador por la ruta más barata.

Cada salida puede declarar un costo, entero mayor o igual que 1. Si no lo declara, vale 100. El costo es el mismo en ambos sentidos. Atravesar una salida es una acción cuyo costo base es el de esa salida (en lugar del 100 fijo de P1 §2.3). El intervalo es max(1, costo_salida * 100 // velocidad). Aplica a todos los actores. El costo de atacar, esperar y las demás acciones no cambia. Errantes y rastreadores solo cambian lo que tarda su movimiento.

Se agrega el comportamiento de enemigo «cazador», con un campo rango (entero, en unidades de costo). En su turno, en orden: (1) si comparte sala con el jugador, ataca (P1 §2.8); (2) si no, considera el costo mínimo d de llegar a la sala actual del jugador sumando el costo de cada salida recorrida, usando solo salidas abiertas en ese instante; (3) si no hay ruta, o si d > rango, espera (costo 100); (4) si hay, se mueve un paso por una ruta de costo d, y la acción cuesta lo que la salida que atraviesa.

Desempate: sea u la sala del cazador; entre las vecinas v tales que costo(u,v) + dist(v, jugador) = d, se mueve a la de menor id, sin importar cómo se calcule.

El cazador conoce el esqueleto completo (con costos) y el estado actual de todas las puertas. No le afecta la niebla de guerra del jugador, no abre puertas cerradas y su decisión nunca depende de si el contenido de una sala ya fue descargado.

Equivalencia observable: la decisión en cada turno debe ser idéntica a la que daría un cálculo desde cero en ese instante, aunque entre turnos se abran o cierren puertas, se mueva el jugador, mueran otros actores o cambien velocidades. Se pueden reutilizar cálculos anteriores solo si nunca cambia la decisión.

Rendimiento: el ciclo de eventos entre dos decisiones del jugador toma como máximo 20 ms con decenas de cazadores activos. La decisión de un cazador de rango pequeño no debe costar proporcionalmente al tamaño de la cripta, sino a la región dentro de su rango.

No mencionar estructuras de datos, clases ni módulos.
```

**Requisitos**

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

**Escenarios de aceptación (Apéndice B)**

1. Un cazador sin ruta abierta hacia el jugador espera con costo 100.
2. La ruta más barata cuesta más que su rango: espera con costo 100.
3. Ruta de menos salas pero mayor costo frente a ruta de más salas y menor costo: sigue la de menor costo.
4. Dos vecinas inician rutas de costo mínimo: va a la de menor id.
5. Una puerta de su ruta se cierra entre dos turnos: en el turno siguiente decide como si calculara desde cero.
6. Un actor de velocidad alta atraviesa una salida de costo 1: el intervalo es al menos 1.
7. Cambia la velocidad de un actor que atraviesa una salida costosa: el tiempo restante se escala según P1 §2.3.

**Preguntas para `/speckit.clarify`**

- Si d es exactamente igual a rango, ¿se mueve? (según el texto, sí: espera solo si d > rango).
- ¿Qué cuenta como «abierta en ese instante» para una puerta con cierre automático pendiente?
- ¿El costo d incluye la salida que entra a la sala del jugador? (debería).
- ¿Qué pasa si el cazador y el jugador están en salas vecinas pero la salida está cerrada?
- ¿Hay límite de actores por sala que pueda bloquear el paso?

### Especificación 002: niebla de guerra e «ir a»

**Prompt para `/speckit.specify`**

```
Capacidad: niebla de guerra y viaje automático «ir a». El jugador ya no ve el mapa completo, solo lo que ha explorado, y puede viajar automáticamente dentro de ese conocimiento.

Cada sala está, para el jugador, en uno de tres estados. Explorada: entró al menos una vez (la sala inicial lo está desde el instante 0); conoce nombre, salidas, costo de cada salida y estado de sus puertas según la última observación. Avistada: no explorada, pero es destino de una salida de una sala explorada; solo se sabe que existe una sala detrás. Desconocida: ninguna de las anteriores.

Memoria de puertas: el jugador observa una puerta cuando está en cualquiera de las dos salas que conecta. El mapa del jugador recuerda el estado de cada puerta según su última observación, aunque haya cambiado después (una puerta con cierre automático puede figurar abierta en el mapa y estar cerrada en realidad).

Antorcha (P1 §2.7): mientras esté encendida, al entrar a una sala quedan exploradas todas sus vecinas, por cualquier salida, abierta o cerrada. Eso revela nombre y salidas, no el contenido, y no activa enemigos ni trampas.

Todo lo que la vista muestra y lo que usa «ir a» se deriva exclusivamente del conocimiento del jugador (el programa puede descargar el esqueleto completo como infraestructura). El conocimiento es estado del juego: se guarda en el archivo de partida, se revierte con el pergamino de retroceso y forma parte de la línea de tiempo. Debe existir un comando para ver el mapa conocido: salas exploradas, sus salidas y las salas avistadas.

«ir a <sala>» lleva al jugador a una sala explorada con movimientos ordinarios. La ruta usa solo salas exploradas y salidas que el mapa recuerda abiertas, minimiza la suma de costos y desempata como el cazador (primer paso hacia la vecina de menor id). Cada paso es una acción completa del jugador: consume tiempo según el costo de la salida y entre paso y paso ocurren los eventos del reloj. La ruta se recalcula antes de cada paso con el conocimiento vigente. El viaje se detiene cuando: llega al destino; entra a una sala con enemigos (activos o dormidos); recibe daño; o deja de existir una ruta conocida. No abre puertas aunque tenga la llave. En partida.log cada paso se registra como un movimiento individual y la orden «ir a» como comentario. El pergamino de retroceso revierte solo el último paso.

Rendimiento: un paso de «ir a» se calcula en ≤ 5 ms con el mapa conocido completo de la cripta de referencia; explorar nuevas salas cuesta proporcionalmente a las salas reveladas, no al tamaño del mapa conocido. No mencionar estructuras de datos, clases ni módulos.
```

**Requisitos**

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

**Escenarios de aceptación (Apéndice B)**

1. `ir a` hacia una sala no explorada: se rechaza y no consume tiempo.
2. El mapa recuerda abierta una puerta que en realidad está cerrada: al observarla, el mapa se actualiza y la ruta se recalcula; si no queda ruta, el viaje se detiene sin consumir tiempo adicional.
3. `ir a` entra a una sala con enemigos dormidos: se activan según P1 §2.4 y el viaje se detiene.
4. Con la antorcha encendida, entrar a una sala explora sus vecinas sin activar sus enemigos ni trampas.
5. Un pergamino revierte una entrada con antorcha encendida: las salas exploradas por la antorcha vuelven a su estado anterior.
6. Un pergamino durante un viaje: revierte solo el último paso y el viaje no continúa.

**Preguntas para `/speckit.clarify`**

- ¿Qué pasa si el destino es la sala actual?
- ¿Cómo se registra la causa de detención en la vista (mensaje, código)?
- Si la antorcha se apaga a mitad de viaje, ¿cambia algo?
- ¿Las vecinas exploradas por antorcha hacen avistadas a sus propias vecinas?
- ¿«Recibe daño» incluye daño de trampas y de efectos, o solo de enemigos?
- ¿Una sala con enemigos muertos detiene el viaje?

### Especificación 003: verificación de resolubilidad

**Prompt para `/speckit.specify`**

```
Capacidad: verificación de resolubilidad. Antes de iniciar una partida, el programa determina si la cripta puede ganarse y, si no, explica por qué.

Se usa el esqueleto y la ubicación de las llaves. Supuestos: el jugador puede atravesar cualquier salida abierta y cualquier salida cerrada cuya llave ya obtuvo; las llaves no se consumen; todo enemigo puede ser derrotado; una llave que suelta un enemigo se considera obtenible en la sala donde ese enemigo inicia; las trampas y los cierres automáticos no bloquean, porque una puerta puede volver a abrirse con la misma llave.

Una cripta es resoluble si, partiendo de la sala inicial y bajo esos supuestos, el jugador puede obtener llave_salida y llegar a sala_salida a través de una puerta que la requiere.

Si es resoluble, el resultado es un orden de obtención de llaves en el que cada llave aparece después de todas las llaves necesarias para alcanzarla. Si hay varios órdenes válidos, cualquiera sirve, pero el resultado es determinista (dos ejecuciones dan el mismo orden).

Si no es resoluble, el resultado informa: las llaves que no pueden obtenerse; las puertas de la frontera bloqueada (puertas cerradas adyacentes a la región alcanzable) con la llave que requiere cada una; y dónde se encuentra cada una de esas llaves. Si una llave está detrás de puertas que solo ella abre, directamente o por una cadena de llaves, el reporte señala el ciclo concreto, de forma determinista.

Si la cripta no es resoluble, la partida no inicia salvo que se use --forzar, y se muestra el reporte. La bandera --verificar <cripta> ejecuta solo la verificación, sin instanciar la vista. La interfaz muestra el reporte al iniciar una partida.

Rendimiento: ≤ 200 ms en la cripta publicada más grande. El costo total crece aproximadamente de forma lineal con salas, salidas y llaves; no se repite un recorrido completo por cada llave obtenida, y el reporte sale del mismo recorrido, sin recorridos adicionales por llave. Las llaves se obtienen de la consulta de ubicación de llaves del servicio, que cuenta dentro de presupuesto_solicitudes. No mencionar estructuras de datos, clases ni módulos.
```

**Requisitos**

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

**Escenarios de aceptación (Apéndice B)**

1. `llave_salida` está detrás de la única puerta que ella misma abre: no resoluble; el reporte señala el ciclo.
2. Una llave está en el campo `suelta` de un enemigo errante: la verificación la ubica en la sala inicial del enemigo.
3. Existen varios órdenes válidos de obtención: dos ejecuciones producen el mismo orden.
4. Cripta no resoluble sin `--forzar`: la partida no inicia y se muestra el reporte.

**Preguntas para `/speckit.clarify`**

- ¿Qué criterio concreto hace determinista el orden cuando hay varios válidos (por ejemplo, por id de llave)?
- ¿Qué pasa con una puerta cerrada que no declara llave, o que pide una llave que no aparece en la consulta de llaves?
- ¿Una misma llave puede abrir varias puertas? ¿Y una puerta puede requerir una sola llave siempre?
- Si hay varios ciclos, ¿se reportan todos o uno solo, y con qué criterio?
- ¿Dónde se declaran `llave_salida` y `sala_salida` (según P1)?
- ¿Cómo se presenta el reporte (formato de texto) para `--verificar` y para la interfaz?

### Especificación 004: línea de tiempo

**Prompt para `/speckit.specify`**

```
Capacidad: línea de tiempo. El pergamino de retroceso (P1 §2.11) sigue limitado a 5 acciones. La línea de tiempo es independiente: permite consultar, sin modificar la partida, el estado en cualquier instante desde el inicio.

Estado en el instante t: el estado después de ejecutar todos los eventos con tiempo menor o igual que t. Si a t le corresponde una decisión del jugador, es el estado justo antes de tomarla.

Consulta en partida: el comando «historia <t>» o «historia #k» (estado justo antes de la acción número k del jugador) muestra como mínimo: reloj, sala del jugador, vida y estadísticas, inventario, efectos activos, enemigos de esa sala con su vida, y el mapa conocido en ese momento. La consulta no consume tiempo virtual, no se registra como acción y no altera ningún estado del juego ni del historial de retroceso. Consultar un instante posterior al reloj actual se rechaza.

Consulta sin interacción: --replay partida.log --hasta <t> reproduce la partida hasta t e imprime el mismo resumen sin instanciar la vista. Si t es posterior al final de la partida, muestra el estado final e indica que la partida terminó antes.

Interacción con el retroceso: las acciones revertidas con un pergamino dejan de existir en la línea; la línea describe la historia tal como quedó.

Restricción de memoria: se permiten copias completas del estado (puntos de control), pero no más de una cada K acciones del jugador. K se configura con --checkpoint-cada K; el valor por defecto lo escoge el grupo y lo justifica con mediciones. Una consulta no puede requerir aplicar o deshacer cambios de más de K acciones del jugador. Fuera de los puntos de control solo se almacena la información necesaria para reconstruir los cambios. La memoria total crece con la cantidad de cambios ocurridos más un punto de control cada K acciones, nunca con acciones por tamaño del estado.

Persistencia: guardar y cargar conserva la línea completa. Un archivo de partida de la primera parte se detecta como incompatible o se migra de forma explícita; nunca se carga en silencio.

Rendimiento: «historia» ≤ 50 ms en una partida de al menos 5 000 acciones con K por defecto. Debe medirse memoria y tiempo de consulta con al menos tres valores de K y contra la alternativa sin puntos de control. No mencionar estructuras de datos, clases ni módulos.
```

**Requisitos**

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

**Escenarios de aceptación (Apéndice B)**

1. `historia <t>` con t mayor que el reloj actual: se rechaza.
2. `historia` después de usar un pergamino: no muestra las acciones revertidas.
3. Varios eventos ocurren en el mismo instante t: `historia <t>` muestra el estado después de todos ellos.
4. `historia` no consume tiempo virtual, no se registra en `partida.log` y no modifica el historial de retroceso.
5. `--replay partida.log --hasta t` con t posterior al final: muestra el estado final e indica que la partida terminó antes.
6. Se carga un archivo de partida de la parte 1: se reporta la incompatibilidad o se migra explícitamente; nunca se carga en silencio.

**Preguntas para `/speckit.clarify`**

- ¿Qué pasa con `historia #k` si k es mayor que las acciones realizadas, o k = 0?
- ¿Los pasos de «ir a» cuentan cada uno como acción del jugador para K y para `#k`? (según el enunciado, sí).
- ¿Qué formato tiene el resumen y es el mismo en partida y en `--replay`?
- ¿Qué pasa con t negativo o no entero?
- ¿Cómo se identifica la versión del formato binario para detectar archivos de la parte 1?
- ¿El valor por defecto de K se deja explícitamente abierto en la especificación y se fija en el plan con mediciones?

### Después de cada `/speckit.specify`

1. Corran `/speckit.clarify` con las preguntas de cada bloque y dejen las respuestas registradas en el `spec.md`.
2. Revisen que el `spec.md` no contenga nombres de estructuras, clases ni módulos, y que cada caso del Apéndice B aparezca como escenario.
3. Hagan commit de la especificación **antes** de empezar `plan.md` y antes de cualquier código (§2.6).
4. Anoten cada prompt en `PROMPTS_LLM.md`.
