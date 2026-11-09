# Modelo de datos: conocimiento y viaje

Diseño propuesto, sin implementación. Referencias: [spec](spec.md), [interfaces](contracts/interfaces.md).

## Metadatos estructurales (infraestructura)

`DatosSala`: `id:int`, `nombre:str`, `salidas:tuple[DatosSalida,...]`.

`DatosSalida`: `direccion:N|S|E|O`, `destino:int`, `costo:int`, `puerta_id:Extremo`.

`Extremo`: `(sala_id:int, direccion:str)`. Clave canónica compartida para una salida y su recíproca opuesta declarada; si falta recíproca, conservar su extremo sin inventar conexión. Preparar aliases e índice al iniciar desde esqueleto, fuera de consultas de revelación. No copiar estado mutable de puertas al DTO estructural. El estado actual se observa desde las salidas vivas de la sala ocupada.

Costos positivos/default100/simetría corresponden a 001; no normalizar silenciosamente valores inválidos. Datos incompletos/incoherentes producen error amable antes de iniciar un cruce. IDs no requieren consecutividad ni usar máximo ID como tamaño de arreglo.

## MapaConocido (estado de juego)

| Registro | Campos | Invariantes |
|---|---|---|
| Sala avistada | id, estado=avistada | Sin nombre, contenido ni salidas públicas. |
| Sala explorada | id, estado=explorada, nombre, salidas conocidas | Cada salida guarda dirección/destino/costo/puerta_id; no incluye contenido remoto. |
| MemoriaPuerta | puerta_id, estado=abierta o cerrada | Ausencia de registro equivale a desconocido; se conserva última observación presencial. |
| Revisión de conocimiento | contador entero interno | Invalida proyección de mapa de la UI al cambiar/restaurar registros; no es reloj de juego ni criterio de igualdad histórica. |

Índices propios redimensionables para salas y puertas. No guardar todas las desconocidas. `SalaConocida` no referencia objetos mutables `SalaViva`/`Room` que permitan revelar cambios remotos. `estado.salas`, `salas_visitadas` y contenido precargado permanecen separados.

Transiciones normales: desconocida→avistada→explorada, o desconocida→explorada. Revelación repetida no duplica ni degrada conocimiento. Antorcha explora vecinas inmediatas y avista destinos de sus salidas sin explorarlas recursivamente. Una puerta observada localmente cambia abierta↔cerrada; revelar a distancia no crea observación ni reemplaza la existente. Deshacer puede restaurar cualquier estado anterior, incluida ausencia.

Pedir mapa produce copia/proyección sin mutar. Sala inicial explorada desde t=0; la precarga no causa transiciones. Contenido de la sala actual se muestra por observación física normal, nunca se agrega contenido remoto al mapa.

## CambioConocimiento

Campos: `tipo:sala|puerta`, `clave`, `antes:registro|ausente`, `despues:registro|ausente`. El registro es copia de valores del único elemento afectado, con a lo sumo cuatro salidas para una sala; no una copia del mapa completo.

- Una operación retorna lista ordenada de cambios efectivos; escrituras iguales no generan delta.
- Aplicar hacia adelante en orden; revertir en orden inverso. Revertir ausencia elimina registro. Comparar contenido lógico, no disposición de cubetas ni contador de revisión.
- Adjuntar como `cambios_conocimiento` a la inversa causal de acción/evento existente. No añadir operación a `ACCIONES_JUGADOR` ni gastar una acción extra del tope cinco.
- Apertura/cierre observado se registra junto con la mutación física. Cambios durante drenaje pertenecen al intervalo de la acción que lo inició. Observación inicial no se agrega al undo.
- Una observación de seguridad sin acción nueva debe asociarse al último evento causal del intervalo existente; no crear un intervalo vacío. La actualización habitual en cada evento hace redundante ese refresco en una partida coherente.

Para 004, cada lote incluye `accion_jugador`, `reloj`, orden secuencial de mutación y clase `accion|evento|inicio`. El receptor obtiene cambios antes de su descarte por la pila. Deshacer notifica truncamiento del último intervalo; no vuelve a emitir su inversa como una acción histórica nueva. El receptor de 004 será dueño de su secuencia/índice completo; 002 no requiere conservar todos los lotes en memoria.

## ContextoPaso (transitorio)

`recibio_dano:bool`, `enemigos_vivos_al_entrar:bool`, `movimiento_realizado:bool`, `error:str|None`, `motivo:str|None`.

Se abre para un avance y se acumula durante movimiento/drenaje. Todo daño efectivo>0 lo marca, incluso veneno, quemadura y trampas; la curación no borra el indicador. Detectar enemigos vivos activos/dormidos al entrar antes de su activación o posibles muertes posteriores. No serializar ni usar como historial.

## ControlViaje (transitorio, C2)

`destino:int|None`, `activo:bool`, `ultimo_motivo:Motivo|None`. No guardar ruta planificada ni consultar grafo vivo para decidirla.

Estados: inactivo→activo por orden válida; activo→activo tras paso completo seguro; activo→inactivo al detener/cancelar/deshacer/guardar/pausar/fin/error del viaje o al instalar una carga válida. Orden al destino actual devuelve destino alcanzado sin activar el controlador. Un destino avistado/desconocido se rechaza sin tiempo ni acciones. Consultar mapa, foto, inventario o ayuda conserva el viaje. Una acción manual cancela continuación antes de procesarla; cargar una partida es una excepción: solo cancela al instalarla correctamente, y un fallo conserva el viaje anterior incluso al gestionar su error en la interfaz.

`Motivo`: `destino`, `enemigos`, `dano`, `sin_ruta`, `cancelado`, `fin_partida`, `error`. Si coinciden, prioridad de presentación: fin_partida, dano, enemigos, destino, cancelado, sin_ruta, error. La cancelación solicitada durante un paso se hace efectiva al finalizar sus eventos; no se interrumpe una acción del motor a medias.

## ResultadoRuta (transitorio)

`alcanzable:bool`, `costo_total:int|None`, `primer_vecino:int|None`, `direccion:N|S|E|O|None`.

Si origen=destino: costo0 y sin dirección. Si no hay ruta: costo/dirección ausentes. La adyacencia solo entrega exploradas conectadas por puertas recordadas abiertas, con costos positivos; el planificador no recibe mapa vivo ni proveedor de contenido.

## Serialización y compatibilidad

En core v3: `conocimiento:{salas:[registros], puertas:[registros]}`; claves de extremo se codifican como dos campos, nunca como claves JSON de objetos. Ausencia de memoria representa estado de puerta desconocido. Deltas en inversas guardan antes/después y presencia explícita. Exportación/importación manual del índice, sin confiar en `dataclasses.asdict` para estructuras propias.

Validar duplicados, estados, IDs/destinos existentes en metadatos, direcciones, costos y referencias de puertas antes de instalar la partida cargada. Incompatibilidad de versiones/registro faltante no se rellena con una niebla inventada. Conservar acceso indexado a salas en el binario. No serializar ControlViaje, ContextoPaso, heap, distancias o caché visual.

004 añadirá registro histórico completo/checkpoints mediante el contrato acordado; este documento no implementa esa capacidad ni decide K. La forma de serialización solo usa dicts como envoltorios JSON, no como índices del problema evaluado.
