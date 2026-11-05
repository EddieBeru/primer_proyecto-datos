# Capacidades de la parte 2

## Terreno y cazador

Desde el punto de vista del juego, las salidas ahora tienen un costo de tránsito
y aparece un enemigo que persigue al jugador por la ruta más barata.

Cada salida puede declarar un costo, entero mayor o igual que 1. Si no lo declara,
vale 100. El costo es el mismo en ambos sentidos. Atravesar una salida es una
acción cuyo costo base es el de esa salida (en lugar del 100 fijo de P1 §2.3).
El intervalo es `max(1, costo_salida * 100 // velocidad)`. Aplica a todos los
actores. El costo de atacar, esperar y las demás acciones no cambia. Errantes y
rastreadores solo cambian lo que tarda su movimiento.

Se agrega el comportamiento de enemigo «cazador», con un campo rango (entero,
en unidades de costo). En su turno, en orden:

1. Si comparte sala con el jugador, ataca (P1 §2.8).
2. Si no, considera el costo mínimo `d` de llegar a la sala actual del jugador
   sumando el costo de cada salida recorrida, usando solo salidas abiertas en ese
   instante.
3. Si no hay ruta, o si `d > rango`, espera (costo 100).
4. Si hay, se mueve un paso por una ruta de costo `d`, y la acción cuesta lo que
   la salida que atraviesa.

Desempate: sea `u` la sala del cazador; entre las vecinas `v` tales que
`costo(u,v) + dist(v, jugador) = d`, se mueve a la de menor id, sin importar cómo
se calcule.

El cazador conoce el esqueleto completo (con costos) y el estado actual de todas
las puertas. No le afecta la niebla de guerra del jugador, no abre puertas
cerradas y su decisión nunca depende de si el contenido de una sala ya fue
descargado.

Equivalencia observable: la decisión en cada turno debe ser idéntica a la que
daría un cálculo desde cero en ese instante, aunque entre turnos se abran o
cierren puertas, se mueva el jugador, mueran otros actores o cambien velocidades.
Se pueden reutilizar cálculos anteriores solo si nunca cambia la decisión.

Rendimiento: el ciclo de eventos entre dos decisiones del jugador toma como
máximo 20 ms con decenas de cazadores activos. La decisión de un cazador de rango
pequeño no debe costar proporcionalmente al tamaño de la cripta, sino a la región
dentro de su rango.

## Niebla de guerra y viaje automático «ir a»

El jugador ya no ve el mapa completo, solo lo que ha explorado, y puede viajar
automáticamente dentro de ese conocimiento.

Cada sala está, para el jugador, en uno de tres estados:

- **Explorada:** entró al menos una vez (la sala inicial lo está desde el instante
  0); conoce nombre, salidas, costo de cada salida y estado de sus puertas según
  la última observación.
- **Avistada:** no explorada, pero es destino de una salida de una sala explorada;
  solo se sabe que existe una sala detrás.
- **Desconocida:** ninguna de las anteriores.

Memoria de puertas: el jugador observa una puerta cuando está en cualquiera de
las dos salas que conecta. El mapa del jugador recuerda el estado de cada puerta
según su última observación, aunque haya cambiado después (una puerta con cierre
automático puede figurar abierta en el mapa y estar cerrada en realidad).

Antorcha (P1 §2.7): mientras esté encendida, al entrar a una sala quedan exploradas
todas sus vecinas, por cualquier salida, abierta o cerrada. Eso revela nombre y
salidas, no el contenido, y no activa enemigos ni trampas.

Todo lo que la vista muestra y lo que usa «ir a» se deriva exclusivamente del
conocimiento del jugador (el programa puede descargar el esqueleto completo como
infraestructura). El conocimiento es estado del juego: se guarda en el archivo
de partida, se revierte con el pergamino de retroceso y forma parte de la línea
de tiempo. Debe existir un comando para ver el mapa conocido: salas exploradas,
sus salidas y las salas avistadas.

`ir a <sala>` lleva al jugador a una sala explorada con movimientos ordinarios.
La ruta usa solo salas exploradas y salidas que el mapa recuerda abiertas,
minimiza la suma de costos y desempata como el cazador (primer paso hacia la
vecina de menor id). Cada paso es una acción completa del jugador: consume tiempo
según el costo de la salida y entre paso y paso ocurren los eventos del reloj.
La ruta se recalcula antes de cada paso con el conocimiento vigente.

El viaje se detiene cuando:

- Llega al destino.
- Entra a una sala con enemigos (activos o dormidos).
- Recibe daño.
- Deja de existir una ruta conocida.

No abre puertas aunque tenga la llave. En `partida.log` cada paso se registra
como un movimiento individual y la orden «ir a» como comentario. El pergamino
de retroceso revierte solo el último paso.

Rendimiento: un paso de «ir a» se calcula en ≤ 5 ms con el mapa conocido completo
de la cripta de referencia; explorar nuevas salas cuesta proporcionalmente a
las salas reveladas, no al tamaño del mapa conocido.
