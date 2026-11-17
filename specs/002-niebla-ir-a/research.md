# Investigación: 002 — niebla e «ir a»

Fecha: 2026-11-06. Fuentes locales y dos agentes de lectura para estado/historia y rutas/estructuras, según la habilidad. Sin servicio remoto ni mediciones.

## 1. Separar conocimiento e infraestructura

**Decisión:** mapa conocido propio dentro del estado, con registros serializables e índice propio.

**Razón:** `Sesion.iniciar` descarga plano completo y `ProveedorSesion._precargar_vecinas` incorpora salas dormidas a `EstadoPartida.salas`. Esa pertenencia no distingue conocimiento. `salas_visitadas`/`SalaViva.visitada` significan entrada física y puntaje/rastro.

**Alternativas:** filtrar salas cargadas revela infraestructura; usar visitas pierde antorcha; copiar plano por acción incumple memoria/reversión.

Fuentes: `src/orchestrator/sesion.py`, `src/controller2/modelo.py`; FR-NIE-01–08.

## 2. Revelación, observación e identidad de puertas

**Decisión:** K1 propuesto agrega `datos_sala(id)` solo de metadatos, desde índice propio preparado por Sesión una vez. No usar `sala_lista` para revelar. Puertas sin observación presencial tienen estado desconocido; antorcha conserva observaciones remotas anteriores.

**Razón:** `RoomLoader.plano` ya trae nombre/salidas; `sala_lista` hidrata contenido y precarga. Las respuestas 1/3 distinguen revelar sala de observar puerta. Actualizar conocimiento únicamente en inicialización/acciones/eventos, no en fotos o consultas.

**Alternativas:** revelar puertas a distancia contradice respuesta 1; consultar puertas vivas al planificar filtra conocimiento oculto.

Identificar extremos por `(sala_id, dirección)`. Si el plano declara salida recíproca opuesta hacia el origen, compartir clave canónica, menor extremo lexicográfico. No fusionar todas las conexiones entre dos IDs ni inventar una arista inversa ausente. La coherencia del estado vivo/costos de salidas recíprocas se coordina con 001: apertura/cierre actuales modifican una salida direccional. B comparte memoria para los extremos recíprocos declarados y prueba observación desde ambos lados.

Fuentes: `src/models/rooms.py`, `src/controller2/movimiento.py`, aclaraciones de spec.

## 3. Estructuras y Dijkstra

**Decisión:** tabla hash redimensionable propia y heap binario propio en `src/estructuras/`; Dijkstra neutral en `src/algoritmos/rutas.py`, adyacencia inyectada. Almacenamiento `list`, registros tipados, hash determinista de claves enteras/tuplas. Rehash al superar carga0,75 duplicando capacidad, sin dict paralelo.

**Razón:** `controller1.TablaHash` tiene cubetas fijas y nodos LRU, y C2 no debe importarla. La agenda mezcla prioridad con eventos/cancelaciones y no es una cola genérica. No existe Dijkstra/heap reutilizable. Índices temporales solo de nodos descubiertos evitan limpiar toda la cripta por paso o reservar hasta el ID máximo.

**Algoritmo:** relajar etiquetas `(costo, primer_vecino_id)`; el primer arco fija primer vecino y dirección. Igual costo acepta menor primer vecino. Orden de heap: etiqueta, ID nodo, secuencia. Inserciones duplicadas y descarte de obsoletas, sin decrease-key. Costos positivos permiten terminar al extraer destino vigente. Arcos paralelos hacia el mismo vecino usan orden N,S,E,O como desempate técnico estable.

**Alternativas:** BFS no pondera; cola ordenada lineal encarece relajaciones; heapq sustituye estructura evaluada; caché de cazadores usa grafo/puertas distintos. A puede reutilizar el núcleo neutral sin compartir resultados, pero B no depende de su estrategia por rango. Comparar heap propio con cola lineal en bench y justificar con datos posteriores.

**Ajuste aceptado 2026-11-08:** el costo de revelación se evalúa como esperado amortizado sobre los registros de salas/puertas consultados o modificados. Las operaciones ordinarias no barren el mapa conocido; el rehash puede recorrer los registros del índice. Las mediciones incluyen secuencias con expansiones y su trabajo total, sin excluirlas de SC-NIE-02. El límite de 5 ms para calcular cada paso permanece; el acuerdo sigue pendiente de contraste con el enunciado íntegro P2.

Fuentes: enunciado §7, constitución III, FR-NIE-11 y FR-CAZ-01/02/09. No refactorizar todos los dict/set históricos.

## 4. Deltas y antorcha

**Decisión:** cambios efectivos con antes/después y ausencia explícita, adjuntos a la inversa causal; receptor opcional para 004 antes del descarte de la pila acotada.

**Razón:** `PilaDeshacer` corta en miembro de `ACCIONES_JUGADOR` y descarta tras cinco intervalos. Un delta colocado fuera de su acción queda en otro intervalo; la pila no conserva historia completa. 002 define cambios de conocimiento bidireccionales; 004 conserva el registro completo/checkpoints.

**Hallazgo:** `efectos.usar_antorcha` guarda objeto/evento nuevo; su inversa no restaura el efecto anterior. Capturar presencia/valor anterior y eventos reemplazados; probar encendido, reencendido, apagado y undo sin alterar consumo/duración P1.

**Alternativas:** snapshot por acción prohibido; solo inversas no reproducen hacia adelante; reconstruir desde visitas pierde antorcha y puertas recordadas.

Fuentes: `src/controller2/deshacer.py`, `efectos.py`, `fachada.py`; FR-NIE-08/17, FR-LIN-07–12.

## 5. Viaje cancelable y controles

**Decisión:** control transitorio C2 y un movimiento/drenaje por avance de Sesión. Pygame atiende entradas antes de cada avance; consola usa espera de entrada breve e interrumpible. Registrar daño y enemigos al entrar durante el intervalo.

**Razón:** `Sesion.paso` ya delimita acción/eventos. Vida neta puede ocultar daño curado; enemigos pueden morir antes de foto final. `_mover_libre` es visual gratuito y `_revisar_puerta` dispara cruce manual. Automático emite intención de motor sin simular píxeles.

**Alternativas:** confirmar toda puerta cambia modo manual; bucle síncrono completo impide cancelar; reanudar al cargar/guardar/pausar genera movimientos inesperados.

Controles elegidos: M abre mapa, flechas seleccionan y Enter viaja. Escape cancela viaje activo, o cierra mapa, o pausa según contexto. Movimiento manual fuera del mapa cancela primero; U cancela y deshace. Consultar mapa, foto, inventario o ayuda conserva el viaje. Guardar y pausar cancelan; cargar solo cancela al instalar correctamente la partida, mientras su fallo conserva el viaje anterior incluso después de mostrar el error. No requiere confirmación nueva al cruzar manualmente.

Prioridad de mensaje si coinciden causas: fin_partida, daño, enemigos, destino, cancelado, sin_ruta, error. No cambia eventos ni su orden. Destino actual termina inmediatamente antes del bloqueo inicial por enemigos. La espera visual no consume reloj virtual.

Fuentes: `src/view/app.py`, `src/view/entrada.py`, `src/orchestrator/sesion.py`; FR-NIE-12–18/21.

## 6. Persistencia y replay

**Decisión:** proponer v3 P2 con mismo índice/core/blobs; conocimiento en core, deltas dentro de inversas. Rechazar v1/v2 en carga P2 explícitamente; no reconstruir niebla perdida. Viaje no se serializa y guardar cancela continuación. 004 ampliará este contrato antes de integrar historia; cambio incompatible posterior exige versión explícita.

**Razón:** savegame actual VERSION_FMT=2; `EstadoPartida.a_dict` usa asdict, insuficiente para serializar el nuevo índice. Usar exportación/importación explícita y validar antes de reemplazar la partida activa. Mantener acceso indexado por sala.

**K3:** reconocer comentario estricto `#ir-a <entero>` en parser, memoria y ambos replay. Saltarlo sin iniciar viaje; reproducir movimientos individuales. No registrar consultas/cancelación como acciones.

**Alternativas:** conservar versión con semántica incompatible da carga silenciosa; migrar desde visitas inventa conocimiento; reproducir orden automática más pasos duplica acciones.

Revisión de integración: `cargar_en_frio` inicia antes de cargar; validar formato primero y preparar sesión candidata para instalar solo tras validar versiones/conocimiento/catálogo. Fallos conservan la sesión previa; solicitudes reales de validación no se revierten. La proyección de mapa se ordena en Sesión con mergesort, sin reutilizar la inyección `orden_fn` de inventario, cuya firma es distinta. Detectar cancelación manual por KEYDOWN y por teclas sostenidas antes del avance automático.

Extraer registros cuesta O(Vconocido+Econocido); construir la proyección ordenada cuesta O(Vconocido log Vconocido+Econocido). La vista reutiliza esa proyección mientras el panel esté abierto y no cambie la revisión del conocimiento.

Fuentes: `src/controller1/savegame.py`, `src/controller2/modelo.py`, `src/controller2/bitacora.py`, `Sesion.reproducir`.

## 7. Dependencias y validación

- 001 es dueño de costos y duración; hoy Exit/SalidaViva carecen de costo. Contrato de integración: entero≥1/default100/simétrico. Falsos ponderados prueban B aisladamente; aceptación integrada espera esos cambios, sin duplicar cálculo temporal.
- 004 decide K/checkpoints y registro completo. Aquí solo conocimiento serializable y cambios ordenados; no implementar historia/--hasta. Los falsos validan la entrega aislada; T052 condiciona la aceptación completa de FR-NIE-08 a verificar conocimiento histórico, retroceso y persistencia con004 real.
- Bench: semilla20261106; tamaños100/1 000/10 000; 100 calentamientos y1 000 consultas por carga. Mediana/p95/máximo, operaciones y memoria; no usar mínimo de tres de `_mide` como única evidencia.
- Incógnitas técnicas resueltas para diseño. Aceptación de contratos y contraste con documento oficial P2 son condiciones externas explícitas, no obtenidas.
- Las aprobaciones se registran por contrato en T001; K1 aprobado y enmendado permite T018 sin completar K2/K3/K5. La aceptación de los ajustes documentales del 2026-11-08 no sustituye la aceptación del compañero.
- Python3.12.3 disponible; pytest ausente en .venv. Documentar preparación, sin instalar paquetes ni atribuir resultados en este workflow.

## Estado de integración al iniciar implementación — 2026-11-08 (T002)

Revisión del código local, sin consultar remotos: `src/models/rooms.py:Exit` y
`src/controller2/modelo.py:SalidaViva` todavía no exponen costo de salida. El motor
conserva movimiento ordinario de costo100 y `src/controller2/reloj.py:intervalo`
ya calcula `max(1,costo*100//velocidad)`. No existe núcleo Dijkstra/heap neutral
reutilizable en `src/`. La entrega ponderada y la coherencia física de puertas
recíprocas de001 siguen pendientes de verificación con A (T046).

Se conserva la decisión base: desarrollar estructuras y núcleo neutrales para B,
con costos positivos explícitos en los falsos. B consume costo entero≥1/default100,
simetría y duración ordinaria cuando001 los entregue; no implementa cazadores ni
duplica la fórmula temporal. Esta constatación local no equivale a un acuerdo nuevo
con el compañero ni afirma haber verificado su trabajo remoto. K1/K2/K3/K5 siguen
sin aceptación registrada para002; sus cambios permanecen bloqueados por T001.

Actualización2026-11-08: después del registro inicial, el usuario autorizó
K1/K2/K3/K5 mediante «apruebo todos los contratos». Enmienda002 en CONTRATOS.md;
no se atribuye esa frase a otra persona. La integración real001/004 sigue pendiente.


## Contraste con fuente oficial aportada — 2026-11-09

Leído `docs/Cripta Parte II.md` completo tras la indicación del usuario. La falta
de fuente P2 queda resuelta para002. §§3.3–3.4 confirman los estados, memoria
presencial, revelación con antorcha sin contenido/activación, rutas por conocimiento,
recalcular por paso, detenciones, log y undo. §5.3 confirma la proporcionalidad
de exploración y el registro reversible; §6.1 fija5 ms en el mapa completo de la
referencia; §6.2 confirma las prohibiciones y §6.3 exige medir mapa/ir a con
sintéticos por semilla. Apéndice B contiene exactamente los seis primeros casos
de la especificación. §7.3 exige mapa, comando y motivo de detención.

No aparece una contradicción esencial nueva: los casos añadidos por aclaración
(efecto inmediato al encender, estados desconocidos de puertas remotas, enemigos
iniciales y cancelación) permanecen como acuerdos del usuario para comportamientos
no desarrollados explícitamente en el enunciado. La proporcionalidad se documenta
como esperada amortizada, contando el rehash. No se afirma haber recibido la
cripta de referencia junto con el enunciado; ese bloqueo continúa independiente.

§2.5 exige que las pruebas citen IDs de requisito: se añadieron referencias a
los casos automatizados y se mantiene la matriz requisito→tarea→prueba debajo.
Las notas anteriores sobre fuente ausente son fotografías históricas.


## Ajuste del método de medición — 2026-11-09

La primera matriz exhaustiva de36 cargas por1000 consultas en cada alternativa
resultó impráctica: la prueba piloto de una búsqueda de10000 salas superó400 ms,
lo que implicaba decenas de minutos solo en una parte de la matriz. Se interrumpió
esa ejecución sin publicar resultados agregados inexistentes. El diagnóstico de
1000 consultas sobre tres mallas sí terminó; se conserva separado porque usaba
la primera generación de grafos dirigidos, anterior a corregir los costos
recíprocos. No se presenta como una cripta válida ni como referencia oficial.

Se revisó el plan de medición, no los requisitos del juego: la matriz conserva36
cargas, tamaños, formas, estados de conocimiento, semilla y ambas alternativas.
El muestreo predeterminado es1000/100/10 para100/1000/10000 salas, con100/10/1
calentamientos. Se publican tamaño de muestra, mediana, p95, máximo, memoria y
fallos; p95 con10 muestras es aproximado y no sirve para certificar el límite
oficial. Se puede pasar `muestras=1000` explícitamente a las funciones para una
corrida extensa. P2§6.3 no prescribe1000 repeticiones; era una decisión del plan.

La generación final usa costos positivos iguales en extremos recíprocos, misma
identidad de puerta y grado≤4, comprobados con tests. El caso desactualizado
recuerda cierres mientras el estado físico de referencia está abierto; la ruta
no recibe ese estado físico. Se optimizó la adyacencia moviendo la consulta de
destino después del filtro por dirección: una consulta por salida en vez de
cuatro. Se conservan desempate N,S,E,O, decisiones y complejidad asintótica.
