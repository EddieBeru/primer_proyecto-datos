# Data Model: Línea de tiempo (004)

## Registro histórico

Un registro es una mutación reversible de C2, en el orden exacto en que ocurrió.
No contiene una copia del estado completo. Se construye a partir del formato
inverso que ya usa `PilaDeshacer`, extendido para conservar todas las acciones y
eventos, no solo los cinco intervalos reversibles.

Campos conceptuales:

- `secuencia`: posición cronológica dentro de la línea vigente.
- `reloj`: reloj virtual asociado al cambio.
- `fase`: evento automático, decisión del jugador o consumo del pergamino.
- `accion`: ordinal de la acción de línea asociada, si aplica.
- `inversa`: delta necesario para volver al estado anterior, incluidos eventos
  programados/cancelados, conocimiento, RNG y cambios de entidades.

La pila P1 continúa siendo independiente y conserva su tope de cinco intervalos;
el ordinal de línea de tiempo no reemplaza el contador de acciones del motor.

## Checkpoint

Punto completo de reconstrucción, con el estado serializable de C2, la posición
de registro que cubre y el número de acción de la línea en ese punto. Se conserva
uno al inicio y otro cada K acciones aceptadas de la línea. El estado actual tras
la última acción es el extremo más reciente. No se guarda un checkpoint por
evento ni por acción fuera del intervalo K.

## Línea vigente

Mantiene K, la secuencia de registros inversos, los checkpoints y el número de
acciones que sobreviven en la rama vigente. Cada paso de viaje y cada acción
aceptada que cambia la partida incrementa el ordinal; el uso aceptado del
pergamino se agrega después de truncar los intervalos revertidos. Las acciones
eliminadas y sus checkpoints posteriores se descartan. Los ordinales de las
acciones supervivientes permanecen consecutivos desde 1.

## Corte de consulta

Punto lógico solicitado por tiempo `t` o acción `#k`:

- `t`: después de eventos automáticos con reloj ≤ t y antes de la primera
  decisión del jugador en t de la línea vigente.
- `#k`: estado justo antes de la acción k; `k` empieza en 1 y debe existir.

El corte identifica el registro y checkpoint posteriores más cercanos para
reconstruir sin modificar el juego activo. El trayecto de reconstrucción cubre a
lo sumo K acciones de línea.

## Resumen histórico

Proyección inmutable del estado reconstruido: reloj, sala, vida y estadísticas,
inventario, efectos activos, enemigos de la sala y conocimiento del mapa.
Consultas y renderizadores consumen esta proyección y no reciben referencias al
estado activo ni a objetos vivos del motor.

## Persistencia

El bloque de línea serializa K, ordinal vigente, registros y checkpoints. La
carga valida tipos, orden, offsets, rangos de acción, intervalos entre
checkpoints y coherencia con el estado actual antes de instalarla. Los archivos
P1 y P2 pre-004 sin este bloque se rechazan explícitamente en el flujo P2.
