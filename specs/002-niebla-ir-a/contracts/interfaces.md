# Propuesta de interfaces: 002

Estado: **aprobación explícita del usuario registrada el 2026-11-08**: «apruebo todos los contratos». Enmienda incorporada en `CONTRATOS.md` con esa evidencia directa, sin atribuir un mensaje a otra persona. La implementación sigue las interfaces acordadas aquí; las dependencias reales de001/004 y el contraste oficial P2 permanecen pendientes.

## K1: metadatos sin contenido

Extender el protocolo que C2 recibe por inyección:

```text
datos_sala(id:int) -> DatosSala
sala_lista(id:int) -> SalaViva     # existente, solo entrada/hidratación normal
```

`DatosSala`/`DatosSalida` se definen en [data-model.md](../data-model.md), con tipos neutrales en `src/models/`. `ProveedorSesion` adapta `RoomLoader.plano` a un índice propio de metadatos preparado una vez, sin llamadas HTTP nuevas. Falsos implementan igual protocolo. La consulta de metadatos no agrega salas vivas, enemigos, trampas, visitas, solicitudes ni fichas a caché. ID inexistente devuelve error de dominio; no fabricar datos.

C2 no importa C1. El estado vivo de puertas se observa en la sala ocupada; el DTO estructural no entrega estado mutable remoto. La identidad de extremos/aliases se normaliza una vez. Coordinación con A: costo y estado físico de puertas recíprocas deben ser coherentes desde ambos extremos; hoy el código solo cambia una salida direccional. La implementación compartida de esa coherencia debe incorporarse al acuerdo de integración 001/002 antes de aceptar pruebas de cruce bidireccional.

## K5: mapa, órdenes y pasos

Mantener `Sesion.paso(texto, grabar=True) -> (ok, mensaje, FotoEstado)`. Incorporar comandos exactos:

| Texto | Efecto |
|---|---|
| `ir a <id>` | Valida/prepara viaje; no ejecuta una ruta completa en esta llamada, no consume tiempo. |
| `cancelar` | Cancela continuación activa, sin tiempo ni undo. Si no hay viaje, éxito sin efecto. |
| `deshacer` | Cancela continuación antes de usar la operación existente; revierte último paso ordinario. |

`<id>` es entero decimal. Sintaxis incompleta, ID no existente o destino no explorado: rechazo sin tiempo ni cambios en pila/acciones. Destino actual: éxito inmediato sin movimiento. Si necesita movimiento y hay enemigos vivos en sala actual: rechazo sin tiempo. Una acción manual distinta cancela el viaje antes de procesarse; un nuevo `ir a` sustituye el anterior tras cancelar. Consultar mapa, foto, inventario o ayuda conserva el viaje. Guardar y pausar lo cancelan. Cargar solo cancela al instalar correctamente la partida; una carga fallida conserva el viaje anterior, incluso al gestionar su error en la interfaz.

Métodos nuevos propuestos en Sesión:

```text
mapa_conocido() -> MapaDTO
avanzar_viaje(grabar=True) -> (ok, mensaje, FotoEstado)
```

El comando de consola `mapa` llama `mapa_conocido()`, sin pasar por drenaje. La vista usa el mismo método. `ir a`/`cancelar` son controles y deben retornar antes del `_drenar` genérico; no consumir ni reordenar un turno pendiente como efecto lateral. `avanzar_viaje` pide a C2 calcular/validar siguiente movimiento, lo ejecuta por el camino ordinario y drena una sola vez, captura contexto del intervalo y devuelve foto. No llamar recursivamente a toda la orden `ir a` ni duplicar drenaje. Inactivo: éxito sin movimiento.

C2 posee reglas de ruta/continuación/detención; Sesión coordina, no decide si una puerta/daño habilitan viajar. Nueva API de C2 propuesta:

```text
Fachada.iniciar_viaje(destino) -> (ok,mensaje)
Fachada.cancelar_viaje() -> (ok,mensaje)
Fachada.preparar_paso_viaje() -> ResultadoRuta
Fachada.finalizar_paso_viaje(contexto) -> estado de viaje
```

No sustituir daño efectivo por diferencia neta de vida. Observar puertas locales a tiempo; si una salida real rechaza un movimiento, actualizar recuerdo y recalcular sin costo temporal por rechazo. Una ruta imposible/error detiene el controlador y publica motivo; jamás abrir puertas ni girar en un bucle de reintentos.

### Proyecciones públicas

Ampliar `FotoEstado` con `viaje:{activo,destino,motivo}` y `conocimiento_revision:int`. Mantener sus campos actuales; incluir costo en puertas de sala actual, procedente de 001. No adjuntar el plano/mapa completo a cada foto.

`MapaDTO` contiene listas ordenadas por ID de salas exploradas/avistadas y las salidas de exploradas con costos y estado recordado `abierta|cerrada|desconocida`. Avistadas muestran solo ID/etiqueta «sala avistada»; desconocidas no aparecen. No nombres de avistadas, enemigos, suelo, trampas, temporizadores remotos ni estado vivo oculto. Las salidas pueden señalar una avistada sin revelar sus detalles. Retornar valores sin referencias mutables al estado. Ordenar la proyección en Sesión mediante `mergesort(items, clave=...)`, ya disponible en esa capa; C2 entrega registros sin ordenar. No reutilizar `Fachada.orden_fn`: su firma actual es específica del inventario y catálogo.

La foto ordinaria de sala actual conserva contenido observable por presencia física. El mapa remoto y la ruta salen solo de conocimiento. Cachear proyección de mapa por revisión mientras esté abierto; actualizarla al cambiar revisión, incluido deshacer/cargar. No reconstruirla por cada frame de la sala normal.

### Pygame

- M abre/cierra panel de mapa conocido; suspender movimiento por proximidad mientras el panel tiene foco.
- Mostrar lista ordenada de IDs; flechas seleccionan, Enter inicia viaje solo si la sala está explorada y cierra panel. Avistadas identificadas sin nombre no son destinos válidos. Escape cierra mapa.
- Viaje activo: Escape lo cancela sin abrir pausa; una segunda pulsación en modo normal pausa. U cancela y deshace. WASD/flechas fuera de mapa cancelan primero y devuelven movimiento manual; comprobar tanto KEYDOWN como teclas sostenidas de `pygame.key.get_pressed()`, pues el movimiento continuo actual no depende solo de KEYDOWN. No emitir además un paso automático en ese frame.
- Bucle: procesar todos los eventos de entrada, luego a lo sumo un avance si viaje activo y no hay pausa/panel/error/fin. Separar cruces por al menos150 ms reales usando reloj de UI, sin sleep bloqueante ni tiempo virtual. Dibujar cada resultado; no prometer ventana ilimitada para cancelación.
- Al cruzar automáticamente reposicionar junto a puerta opuesta igual que cruce manual y activar `en_puerta`; no llamar `_mover_libre` para disparar cruce automático. La posición visual no forma parte de la ruta ni del undo del motor.
- Guardar y pausar cancelan viaje; instalar una carga válida, iniciar, fin y errores del viaje limpian continuación y temporizador. Una carga fallida conserva el viaje anterior y su temporizador; su error no aplica la limpieza general del viaje. Conservar resto de controles y cruce manual sin confirmación.

### Consola y ejecución sin vista

- Añadir `mapa`, `ir a <id>`, `cancelar` a ayuda.
- Tras iniciar viaje, un controlador del bucle alterna espera cancelable de150 ms y un `avanzar_viaje`, publicando sala/motivo. En Linux usar sondeo de stdin con `select`, con lector/reloj inyectables para pruebas, sin thread que cambie el motor.
- Durante viaje, una línea `cancelar` cancela; una acción manual cancela antes de procesarse. Consultar mapa, foto, inventario o ayuda conserva el viaje. Guardar lo cancela; cargar solo cancela al instalar correctamente la partida, y un fallo conserva el viaje anterior incluso tras mostrar el error. EOF/KeyboardInterrupt cancelan y preservan salida130 existente. Sin viaje, conservar entrada bloqueante actual.
- Para tests/consumidores sin stdin interactivo, llamar explícitamente `avanzar_viaje` y cancelar entre llamadas; no necesitar terminal real ni esperas para probar reglas.

## K3: log y replay

Formato nuevo de comentario, después del header existente:

```text
#ir-a 12
```

Se registra una vez por orden válida aceptada, también si destino ya es actual; órdenes rechazadas no agregan comentario. Los pasos posteriores conservan líneas `reloj|mover|jugador|direccion`. Cancelar/mapa no son acciones ni intervalos nuevos del log.

Extender `parsear`, `BitacoraMemoria`, `reproducir` de C2 y `Sesion.reproducir` para reconocer/ignorar este comentario con sintaxis estricta, sin relajar validación del header ni admitir líneas corruptas arbitrarias. Leer `#ir-a` nunca inicia un viaje. Consecuencias se siguen derivando de los movimientos. Guardado/replay deben producir mismo conocimiento lógico y RNG, sin duplicar pasos.

## K2: persistencia propuesta

- Versión binaria P2 propuesta3; conservar índice de salas/acceso aleatorio y errores de corrupción.
- Core agrega `conocimiento` con listas de registros; inversas agregan `cambios_conocimiento`. Serialización explícita de estructuras propias; no usar asdict para copiar tablas internas.
- Flujo P2 rechaza v1/v2 con `GuardadoError` y explicación de incompatibilidad; no migración automática. Validar conocimiento/metadata/versiones antes de reemplazar partida activa. El lector técnico legado puede mantenerse para diagnóstico, sin permitir carga silenciosa P2.
- Aplicar esa validación tanto a `Sesion.cargar` como a `cargar_en_frio`: comprobar versión/formato antes de iniciar una sesión y preparar estado/proveedores candidatos aislados para validar referencias, versiones y catálogo antes de instalarlos. El `cargar_en_frio` actual llama `iniciar` antes de cargar; modificar ese orden para que una carga fallida conserve la sesión activa, su viaje y su estado lógico. No deshacer solicitudes HTTP ya realizadas durante una validación ni inventar presupuesto recuperado. La cancelación de viaje por cargar se aplica al instalar una carga válida.
- Guardar cancela continuación antes de serializar. Cargar establece controlador inactivo aunque se hubiera guardado en mitad de ruta. No guardar heap, ruta, reloj UI o contexto transitorio.
- La historia completa se incorpora en004; esta propuesta no afirma que el formato ya la contenga. Acordar extensión antes de implementarla y aumentar versión si introduce incompatibilidad.

## Integración con 001 y 004

001 entrega costo/default/validación/simetría y ejecución temporal ordinaria; B no duplica fórmula. Nuevo núcleo neutral `siguiente_paso(origen,destino,adyacentes)` devuelve ResultadoRuta: 002 inyecta adyacencia conocida, A puede usar otro adaptador o algoritmo. No hay requisito de compartir resultados/caché. La prueba end-to-end ponderada espera integrar001; falsos con costos explícitos verifican B independientemente.

004 recibirá receptor opcional `registrar_cambios(contexto,lote)` y `truncar_ultimo_intervalo()` desde el motor mediante inyección, sin importar otra capa ni retener toda historia en002. Registrar antes de descartar inversas por tope cinco. El contexto incluye número de acción, reloj y orden de mutación; datos antes/después aplicables en ambos sentidos. La inicialización permite a004 establecer su origen, sin snapshots por acción. El receptor no puede alterar decisiones del motor; las pruebas de002 usan un colector falso para comprobar orden y truncamiento.

El colector falso permite validar la entrega aislada de 002. La aceptación completa de FR-NIE-08 requiere después una prueba integrada con 004 del conocimiento histórico antes/después de entrada, antorcha y retroceso, incluida su conservación al guardar/cargar (T052); la historia y los checkpoints siguen siendo responsabilidad de 004.
