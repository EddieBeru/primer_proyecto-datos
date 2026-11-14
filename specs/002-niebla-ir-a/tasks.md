# Tasks: Niebla de guerra e «ir a» (002)

**Fecha**: 2026-11-06. **Capacidad**: `002-niebla-ir-a`; rama Git real `main`.
**Revisión**: 2026-11-08; cinco ajustes del análisis aceptados por el usuario, sin implementación.
**Entrada**: [spec](spec.md), [plan](plan.md), [research](research.md), [modelo](data-model.md), [interfaces propuestas](contracts/interfaces.md), [validación](quickstart.md), constitución y CONTRATOS.md con sus enmiendas.
**Estado**: implementación iniciada el 2026-11-08; avance indicado por las casillas y evidencia en quickstart. Una historia: US1, prioridad P1. El usuario autorizó todos los contratos: «apruebo todos los contratos»; enmienda en CONTRATOS.md con esa evidencia directa.

## Formato y condiciones de ejecución

`- [ ] Tnnn [P opcional] [US1 si pertenece a la historia] Acción con ruta exacta`.
Rutas relativas a la raíz; archivos nuevos se crean durante implementación. Cada «Dep.» enumera requisitos previos adicionales; las condiciones de fase también aplican. [P] permite paralelismo únicamente después de resolver sus dependencias y con archivos distintos. Las pruebas se solicitan expresamente y cumplen la constitución; se enumeran antes de implementación para fijar aceptación, sin imponer TDD ni un fallo previo obligatorio.

No usar dict como índice/caché del problema evaluado, heapq/deque/set como sustitutos de estructuras propias, sorted/list.sort para ordenamientos evaluados, ni snapshots por acción. List como almacenamiento y dict como envoltorio JSON/DTO son usos permitidos. No refactorizar colecciones históricas ajenas a 002. C1/C2 no se importan mutuamente; vista→Sesión→motor. No nuevas dependencias de ejecución.

## Fase 1: Preparación y coordinación

**Objetivo**: dejar propuestas y dependencias revisables sin reinicializar el proyecto existente.

- [X] T001 Obtener aceptación explícita para K1/K2/K3/K5 y registrar la enmienda en `CONTRATOS.md`, a partir de `specs/002-niebla-ir-a/contracts/interfaces.md`; registrar estado y evidencia por contrato, incluido el acuerdo de coherencia de puertas recíprocas en K1. Autorización directa del usuario del2026-11-08: «apruebo todos los contratos»; no se atribuye un mensaje al compañero. La aprobación parcial de K1 habilita T018 sin completar K2/K3/K5; el agente no debe contactar al compañero por su cuenta. Requisitos: FR-NIE-03/08/09/16; P2§2.3.
- [X] T002 Documentar en `specs/002-niebla-ir-a/research.md` el acuerdo de integración con 001: A entrega costo entero≥1/default100, simetría y duración ordinaria; B consume esos campos sin implementar cazadores ni duplicar fórmula. Confirmar si A ya entrega un núcleo compatible antes de crear el neutral previsto, evitando duplicación; la decisión base es el núcleo separado descrito en research y no compartir resultados con grafo vivo. Requisitos: FR-NIE-11/12; P2§5.3.
- [X] T003 Registrar en `specs/002-niebla-ir-a/quickstart.md` disponibilidad de pytest y estado de fuentes P2: contrastar con enunciado íntegro al obtenerlo o dejar explícitamente pendiente; no presentar guía como documento oficial. Registrar contradicciones esenciales y bloquear solo las decisiones afectadas; no cerrar aceptación académica sin contraste. Requisitos: P2§2.5 y Apéndice B.

**Condición**: T002/T003 registran estado aunque haya entregables externos pendientes. Cada contrato requiere su aceptación y enmienda antes de modificarlo; T018 solo exige K1. Las otras tareas que dependen de T001 completo conservan esa condición. No se bloquean estructuras neutrales, diseño ni pruebas aisladas.

| Contrato | Estado | Evidencia de aceptación y enmienda |
|---|---|---|
| K1 | Aprobado por el usuario | «apruebo todos los contratos»; enmienda002 en CONTRATOS.md. |
| K2 | Aprobado por el usuario | «apruebo todos los contratos»; enmienda002 en CONTRATOS.md. |
| K3 | Aprobado por el usuario | «apruebo todos los contratos»; enmienda002 en CONTRATOS.md. |
| K5 | Aprobado por el usuario | «apruebo todos los contratos»; enmienda002 en CONTRATOS.md. |

## Fase 2: Fundamentos compartidos

**Objetivo**: infraestructura neutral y datos sintéticos para US1. Depende del registro T002/T003; no exige tener 001 implementada.

- [X] T004 [P] Crear `src/estructuras/__init__.py`, `src/estructuras/tabla_indice.py` y `tests/test_tabla_indice.py`: índice propio para enteros/extremos con hash determinista, consulta/inserción/reemplazo/borrado/iteración; al superar carga 0,75 duplicar capacidad y rehash, sin índice dict auxiliar. Verificar colisiones, borrado, expansión e IDs dispersos sin reservar hasta máximo ID. Requisitos: FR-NIE-19.
- [X] T005 [P] Crear heap binario mínimo neutral en `src/estructuras/monticulo_minimo.py` y `tests/test_monticulo_minimo.py`, con almacenamiento list y prioridad total estable; verificar extracciones, empates y vacío, sin importar controladores ni usar heapq. Requisitos: FR-NIE-11/19.
- [X] T006 [P] Definir DTO inmutables en `src/models/conocimiento.py`: `DatosSala` con `id:int`, `nombre:str`, `salidas:tuple[DatosSalida,...]`; `DatosSalida` con `direccion:N|S|E|O`, `destino:int`, `costo:int`, `puerta_id:Extremo`; `Extremo` como `(sala_id:int, direccion:str)`. Respetar «IDs no requieren consecutividad ni usar máximo ID como tamaño de arreglo» y «no normalizar silenciosamente valores inválidos»; no copiar estado mutable remoto. Requisitos: FR-NIE-03/04.
- [X] T007 Crear fixtures offline reutilizables en `tests/fixtures_niebla.py`, con DTO de T006, costos positivos explícitos, puertas recíprocas/no recíprocas, IDs dispersos, antorcha, trampas, efectos y enemigos vivos/dormidos/muertos; instrumentar metadatos/contenido/activaciones y fallar si revelar o buscar pide contenido. Dep.: T006. Requisitos: FR-NIE-06/07.

**Checkpoint**: índices y heap probados de forma aislada; falsos capaces de verificar B sin entrega de A. La creación de DTO neutrales no cambia todavía el proveedor vigente.

## Fase 3: US1 — Niebla de guerra e ir a (P1)

**Objetivo**: consultar solo conocimiento del jugador y recorrer destinos explorados mediante pasos ordinarios cancelables.
**Prueba independiente**: ejecutar los escenarios 1–11 con proveedor sintético, comparar conocimiento, reloj, RNG, acciones y registros; usar costos explícitos del falso. Esto verifica B; la aceptación temporal integrada espera T046 y la historia completa pertenece a 004.

### Pruebas de comportamiento y contratos

Dependencia común: T004–T007. Estas tareas pueden escribirse contra los contratos propuestos; su aprobación sigue siendo necesaria para implementar interfaces.

- [X] T008 [P] [US1] Crear `tests/test_conocimiento.py`: tres estados, sala inicial t=0, precarga sin revelación, avistada solo ID, consultas sin mutar, puertas locales/remotas, antorcha inmediata/al entrar por puertas abiertas o cerradas y sin contenido/activación remota; incluir escenarios 4,7,9. Requisitos: FR-NIE-01, FR-NIE-02, FR-NIE-03, FR-NIE-04, FR-NIE-05, FR-NIE-06, FR-NIE-07.
- [X] T009 [P] [US1] Crear `tests/test_deltas_conocimiento.py`: deltas efectivos ordenados, restauración de ausencia/conocimiento previo, undo de entrada/encendido/reencendido, efecto anterior y agenda, tope cinco y exclusiones de pergaminos/caché; escenarios 5,10. Requisitos: FR-NIE-06, FR-NIE-08, FR-NIE-17.
- [X] T010 [P] [US1] Crear `tests/test_rutas_conocidas.py`: camino de más arcos y menor costo, empate por primer vecino menor descubierto tarde, ciclos/costo1, arcos paralelos, IDs dispersos, origen=destino y sin ruta; excluir avistadas/puertas desconocidas y detectar consultas a grafo vivo/contenido. Requisitos: FR-NIE-07, FR-NIE-11, FR-NIE-13.
- [X] T011 [P] [US1] Crear `tests/test_viaje.py`: escenarios 1,2,3,6,8,11; muertos no bloquean, dormidos que mueren durante drenaje sí detienen, daño de ataque/trampa/veneno/quemadura seguido de curación detiene, no abrir aun con llave, errores y no reintentar puerta bloqueada en bucle; cancelación sin tiempo ni undo. Requisitos: FR-NIE-05, FR-NIE-10, FR-NIE-12, FR-NIE-13, FR-NIE-14, FR-NIE-15, FR-NIE-17, FR-NIE-18, FR-NIE-21.
- [X] T012 [P] [US1] Extender `tests/test_sesion.py` para K1/K5: metadatos sin red/caché/visitas, controles sin drenaje accidental, un avance con un movimiento/drenaje, mapa sin fugas ni mutaciones, destino actual con enemigos, cancelación manual y límite ordinario de eventos. Requisitos: FR-NIE-03, FR-NIE-09, FR-NIE-10, FR-NIE-12, FR-NIE-14, FR-NIE-21.
- [X] T013 [P] [US1] Extender `tests/test_savegame.py` para K2: roundtrip v3 y deltas, índice por sala, corrupción/duplicados/referencias inválidas, rechazo v1/v2 y ausencia de control de viaje serializado; especificar carga normal/en frío fallida que preserva sesión/viaje, además de carga válida que no reanuda. Requisitos: FR-NIE-08.
- [X] T014 [P] [US1] Extender `tests/test_gamelog.py` para K3: comentario estricto `#ir-a <id>`, una vez por orden aceptada incluso destino actual, ninguno por rechazada; preservar validación header/corrupción, movimientos individuales y replay sin ejecutar orden automática. Requisitos: FR-NIE-16.
- [X] T015 [P] [US1] Extender `tests/test_vista.py` con SDL dummy y reloj falso: selección y datos del mapa, Escape/U, KEYDOWN y teclas sostenidas, cero avance extra tras cancelar, máximo un cruce por actualización/intervalo≥150 ms, reposición/en_puerta y cruce manual por proximidad conservado. Requisitos: FR-NIE-04, FR-NIE-07, FR-NIE-09, FR-NIE-17, FR-NIE-18, FR-NIE-21.
- [X] T016 [P] [US1] Crear `tests/test_consola_viaje.py` con lector/reloj inyectados: mapa, viaje, cancelación entre pasos y acciones manuales; consultar mapa/foto/inventario/ayuda conserva el viaje, guardar cancela, cargar correctamente cancela al instalar y una carga fallida conserva el viaje incluso tras mostrar su error, permitiendo continuar desde el mismo punto. EOF/KeyboardInterrupt→130; ninguna espera real ni terminal/red requeridas. Requisitos: FR-NIE-09, FR-NIE-18, FR-NIE-21.

### Conocimiento, revelación y reversión

- [X] T017 [US1] Implementar `MapaConocido` y registros en `src/controller2/conocimiento.py` e incorporarlo a `src/controller2/modelo.py`: desconocida ausente, avistada «Sin nombre, contenido ni salidas públicas», explorada con nombre/salidas/costos, memoria «Ausencia de registro equivale a desconocido; se conserva última observación presencial». Usar índice propio, copias de valores sin SalaViva/Room mutable y revisión interna que invalida proyección al cambiar/restaurar, sin intervenir en igualdad histórica. Dep.: T004,T006,T008. Requisitos: FR-NIE-01, FR-NIE-03, FR-NIE-04, FR-NIE-19.
- [X] T018 [US1] Implementar K1 `datos_sala(id)` en `src/orchestrator/sesion.py` y adaptar `src/controller1/fake_provider.py` al protocolo acordado: preparar índice de metadatos una vez desde plano, canónico mínimo extremo de recíproca opuesta declarada; no inventar inversa ni fusionar conexiones distintas. Error de dominio por ID inexistente, sin contenido/HTTP/fichas/salas vivas. Dep.: T002,T012,T017 y aceptación de K1 registrada en T001 con su enmienda en `CONTRATOS.md`; no exige completar K2/K3/K5 ni cerrar T001. Requisitos: FR-NIE-03, FR-NIE-05.
- [X] T019 [US1] Inicializar conocimiento y conectar entrada ordinaria en `src/controller2/fachada.py` y `src/controller2/movimiento.py`: sala inicial explorada antes de primera decisión, salidas avistan destinos y cruce observa extremos locales; precarga/visitas no revelan. Inicialización no genera acción deshacible. Dep.: T018. Requisitos: FR-NIE-01, FR-NIE-02, FR-NIE-04.
- [X] T020 [US1] Conectar revelación inmediata al encender y al entrar con antorcha en `src/controller2/fachada.py` y `src/controller2/conocimiento.py`: explorar solo vecinas inmediatas por toda salida, avistar sus destinos sin recursión, conservar memoria de puertas remotas y no activar contenido; apagar no borra conocimiento. Dep.: T019. Requisitos: FR-NIE-06.
- [X] T021 [US1] Registrar observaciones de apertura/cierre y eventos locales en `src/controller2/fachada.py` y `src/controller2/movimiento.py` antes de publicar fotos; cambios remotos conservan última memoria, repetición no duplica ni degrada. Consumir coherencia física de 001, sin implementarla por duplicado. Dep.: T020; cruce bidireccional integrado espera T046. Requisitos: FR-NIE-03, FR-NIE-05.
- [X] T022 [US1] Implementar `CambioConocimiento` en `src/controller2/conocimiento.py` e integrar inversas en `src/controller2/deshacer.py` y `src/controller2/fachada.py`: `tipo:sala|puerta`, `antes:registro|ausente`, `despues:registro|ausente`, copia de único registro con «a lo sumo cuatro salidas para una sala». Aplicar en orden y revertir en orden inverso, adjunto a acción/evento causal, sin nuevo ACCIONES_JUGADOR, intervalo vacío ni snapshot; refresco de seguridad pertenece al evento causal existente. Dep.: T009,T021. Requisitos: FR-NIE-08, FR-NIE-17.
- [X] T023 [US1] Corregir captura e inversa de antorcha en `src/controller2/efectos.py`, `src/controller2/deshacer.py` y `src/controller2/fachada.py`: restaurar presencia/valor anterior del efecto, objeto y eventos reemplazados además de conocimiento; conservar duración/consumo P1 y exclusiones. Dep.: T022. Requisitos: FR-NIE-06, FR-NIE-08.
- [X] T024 [US1] Incorporar receptor opcional inyectado `registrar_cambios(contexto,lote)`/`truncar_ultimo_intervalo()` en `src/controller2/fachada.py` y `src/controller2/deshacer.py`: contexto con acción, reloj, orden y clase `accion|evento|inicio`, emitir antes del descarte por tope cinco y truncar al deshacer sin emitir inversas como nueva historia; no retener archivo/checkpoints en 002. Dep.: T001,T023. Requisitos: FR-NIE-08.

### Rutas y viaje en el motor

- [X] T025 [P] [US1] Crear `src/algoritmos/__init__.py` y `src/algoritmos/rutas.py` con `siguiente_paso(origen,destino,adyacentes)`: Dijkstra neutral sobre índice/heap propios, etiquetas `(costo,primer_vecino_id)`, heap por etiqueta/ID/secuencia, duplicados obsoletos descartados y desempate técnico N,S,E,O para arcos paralelos iguales. `ResultadoRuta` usa `alcanzable:bool`, `costo_total:int|None`, `primer_vecino:int|None`, `direccion:N|S|E|O|None`; «Si origen=destino: costo0 y sin dirección. Si no hay ruta: costo/dirección ausentes». Sin caché ni grafo vivo. Dep.: T002,T004,T005,T006,T010. Requisitos: FR-NIE-11, FR-NIE-19.
- [X] T026 [US1] Implementar adaptador de adyacencia de `MapaConocido` en `src/controller2/conocimiento.py`: entregar solo exploradas conectadas por puertas recordadas abiertas y costos positivos; cada búsqueda usa estado vigente, nunca estado mutable remoto, proveedor de contenido ni mapa de cazadores. Dep.: T021,T025. Requisitos: FR-NIE-07, FR-NIE-11, FR-NIE-13, FR-NIE-19.
- [X] T027 [US1] Crear `src/controller2/viaje.py` con `ControlViaje`: `destino:int|None`, `activo:bool`, `ultimo_motivo:Motivo|None`; validar sintaxis/destino sin tiempo, destino actual termina antes de comprobar enemigos, vivos iniciales rechazan y muertos no bloquean; recalcular por paso, no abrir puertas ni almacenar ruta. Motivos `destino`, `enemigos`, `dano`, `sin_ruta`, `cancelado`, `fin_partida`, `error`; prioridad «fin_partida, dano, enemigos, destino, cancelado, sin_ruta, error». Dep.: T011,T026. Requisitos: FR-NIE-10, FR-NIE-13, FR-NIE-14, FR-NIE-15, FR-NIE-18, FR-NIE-21.
- [X] T028 [US1] Instrumentar `ContextoPaso` en `src/controller2/viaje.py`, `src/controller2/modelo.py`, `src/controller2/fachada.py` y `src/controller2/efectos.py`: `recibio_dano:bool`, `enemigos_vivos_al_entrar:bool`, `movimiento_realizado:bool`, `error:str|None`, `motivo:str|None`; acumular todo daño efectivo>0 sin borrarlo por curación y detectar enemigos antes de activar/morir. Contexto transitorio por avance, sin serialización/historial. Dep.: T027. Requisitos: FR-NIE-12, FR-NIE-14.
- [X] T029 [US1] Exponer iniciar/cancelar/preparar/finalizar viaje en `src/controller2/fachada.py`; resolver bloqueos con observación/recalculo sin tiempo por rechazo ni bucle, completar eventos antes de detener y dar motivo según T027. C2 decide reglas; fallo de carga de contenido durante un cruce detiene con error sin cobrar espera de red, distinto del fallo de cargar una partida que preserva el viaje. Dep.: T001,T024,T028. Requisitos: FR-NIE-12, FR-NIE-13, FR-NIE-14, FR-NIE-15, FR-NIE-17, FR-NIE-21.

### Sesión e interfaces

- [X] T030 [US1] Implementar `ir a <id>`, `cancelar` y `avanzar_viaje(grabar=True)` en `src/orchestrator/sesion.py`, manteniendo triple `(ok,mensaje,FotoEstado)`: controles retornan antes del drenaje genérico; avance ejecuta como máximo un movimiento ordinario, un drenaje y finalización del contexto; inactivo devuelve éxito sin movimiento. Una acción manual cancela antes de procesarse, nueva orden sustituye tras cancelar; consultar mapa/foto/inventario/ayuda conserva el viaje. Guardar/pausar cancelan; cargar solo cancela al instalar correctamente y su fallo preserva el viaje anterior (T037). Dep.: T001,T012,T029. Requisitos: FR-NIE-10, FR-NIE-12, FR-NIE-14, FR-NIE-16, FR-NIE-21.
- [X] T031 [US1] Implementar `Sesion.mapa_conocido()`/`MapaDTO` y ampliar `FotoEstado` en `src/orchestrator/sesion.py`, `src/models/conocimiento.py` y `src/controller2/fachada.py`: listas por ID ordenadas en Sesión con mergesort existente, avistadas solo ID/etiqueta, exploradas con salidas/costos y puertas `abierta|cerrada|desconocida`; sin referencias mutables ni contenido remoto. Foto agrega `viaje:{activo,destino,motivo}` y `conocimiento_revision:int`, sin mapa completo por foto; no reutilizar orden_fn específico de inventario. Dep.: T030. Requisitos: FR-NIE-04, FR-NIE-07, FR-NIE-09, FR-NIE-18.
- [X] T032 [US1] Extender ayuda/render/bucle en `src/orchestrator/consola.py` para `mapa`, `ir a <id>` y `cancelar`, motivo de detención visible y espera cancelable de150 ms con select en Linux y lector/reloj inyectables; alternar entrada y avance sin threads que muten motor. Consultar mapa/foto/inventario/ayuda conserva el viaje; una acción manual cancela antes de procesarse, guardar cancela y cargar solo cancela al instalar correctamente. Mostrar el error de una carga fallida preservando el viaje anterior, sin aplicar limpieza general. Conservar entrada bloqueante sin viaje y EOF/KeyboardInterrupt→130. Dep.: T016,T031. Requisitos: FR-NIE-09, FR-NIE-18, FR-NIE-21.
- [X] T033 [US1] Agregar panel conocido en `src/view/app.py` y `src/view/ui.py`: M abre/cierra, flechas seleccionan, Enter solo acepta explorada y cierra panel, Escape lo cierra; suspender proximidad con foco. Proyección cacheada por revisión solo mientras abierto, sin nombres de avistadas/contenido remoto. Dep.: T015,T031. Requisitos: FR-NIE-07, FR-NIE-09, FR-NIE-18.
- [X] T034 [US1] Integrar avances cancelables en `src/view/app.py` y `src/view/entrada.py`: entradas antes de avance, Escape cancela viaje antes de pausa, U cancela y deshace, WASD/flechas fuera del panel cancelan tanto KEYDOWN como get_pressed sin avance automático extra ese frame; máximo un cruce/update con separación real≥150 ms y reloj UI sin sleep. Reposicionar como cruce manual y activar en_puerta, limpiar temporizador al terminar, mantener cruce manual sin confirmación. Dep.: T033. Requisitos: FR-NIE-18, FR-NIE-21.

### Persistencia, replay y ciclo de vida

- [X] T035 [US1] Implementar exportación/importación explícita de conocimiento y deltas en `src/controller2/modelo.py`, `src/controller2/conocimiento.py` y `src/controller2/fachada.py`: core `conocimiento:{salas:[registros], puertas:[registros]}`, extremos como dos campos, antes/después con presencia; validar duplicados/estados/IDs/destinos/direcciones/costos/referencias contra metadatos. No asdict de índices, memoria desconocida ausente, ni serialización de ControlViaje/ContextoPaso/heap/distancias/caché visual. Dep.: T013,T024,T031. Requisitos: FR-NIE-08.
- [X] T036 [US1] Implementar formato P2 v3 en `src/controller1/savegame.py` conservando índice de salas y errores de corrupción; rechazar v1/v2 con GuardadoError explicativo en flujo P2, sin migración ni reconstrucción de niebla. Mantener lectores técnicos legados solo si no permiten carga P2 silenciosa. Dep.: T001,T035. Requisitos: FR-NIE-08.
- [X] T037 [US1] Hacer carga normal y en frío atómicas en `src/orchestrator/sesion.py`: comprobar formato antes de iniciar y preparar estado/proveedores/catálogo candidatos; validar todo antes de instalar. Fallo conserva sesión activa, conocimiento y viaje, sin fingir reversión de solicitudes HTTP; éxito instala con viaje inactivo. Dep.: T036. Requisitos: FR-NIE-08.
- [X] T038 [US1] Incorporar comentario `#ir-a <id>` y replay en `src/controller2/bitacora.py` y `src/orchestrator/sesion.py`, revisando `src/controller1/gamelog.py` solo si su validación lo requiere: parser, memoria y ambos reproductores lo reconocen estrictamente y lo ignoran al reproducir; registrar una vez por orden válida y movimientos normales por paso, sin acciones para mapa/cancelar ni duplicación automática. Dep.: T001,T014,T030. Requisitos: FR-NIE-16.
- [X] T039 [US1] Unificar limpieza de continuación en `src/controller2/fachada.py`, `src/orchestrator/sesion.py` y `src/view/app.py`: deshacer cancela y revierte último intervalo, guardar cancela antes de serializar, pausar/iniciar/fin y errores del viaje detienen; consultas de mapa/foto/inventario/ayuda conservan el viaje. Carga válida cancela al instalar; una carga fallida preserva viaje y temporizador anterior incluso al mostrar su error, sin ejecutar limpieza general de continuación. No reanudar silenciosamente tras una carga válida. Dep.: T032,T034,T037,T038. Requisitos: FR-NIE-17.

### Verificación de US1 y mediciones

- [X] T040 [US1] Ejecutar y resolver fallos de `tests/test_tabla_indice.py`, `tests/test_monticulo_minimo.py`, `tests/test_conocimiento.py`, `tests/test_deltas_conocimiento.py`, `tests/test_rutas_conocidas.py` y `tests/test_viaje.py` offline; conservar invariantes/contratos y registrar comando/resultado en `specs/002-niebla-ir-a/quickstart.md`. Dep.: T039. Requisitos: FR-NIE-01, FR-NIE-02, FR-NIE-03, FR-NIE-06, FR-NIE-11, FR-NIE-13, FR-NIE-14, FR-NIE-15, FR-NIE-17.
- [X] T041 [US1] Ejecutar y resolver fallos de `tests/test_sesion.py`, `tests/test_consola_viaje.py` y `tests/test_vista.py` con SDL dummy, lector/reloj falso; verificar escenarios 1–11 sin esperas reales, daño curado, enemigos muertos durante drenaje y teclas sostenidas. Verificar desde el bucle de consola que mapa/foto/inventario/ayuda conservan el viaje y que una carga fallida permite continuar desde el mismo punto, incluso tras mostrar el error; una carga válida no reanuda. Registrar resultados en `specs/002-niebla-ir-a/quickstart.md`. Dep.: T040. Requisitos: FR-NIE-04, FR-NIE-07, FR-NIE-09, FR-NIE-10, FR-NIE-12, FR-NIE-14, FR-NIE-17, FR-NIE-18, FR-NIE-21.
- [X] T042 [US1] Completar y ejecutar roundtrip/undo tras carga en `tests/test_savegame.py` y replay de ambos caminos en `tests/test_gamelog.py` y `tests/test_sesion.py`, comparando sala/reloj/RNG/conocimiento lógico; probar cargas normal/en frío fallidas y exitosa sin reanudar. Registrar resultados en `specs/002-niebla-ir-a/quickstart.md`. Dep.: T041. Requisitos: FR-NIE-08, FR-NIE-16.
- [X] T043 [US1] Añadir y ejecutar colector falso 004 en `tests/test_deltas_conocimiento.py`: deltas bidireccionales por acción/evento/inicio en orden y truncamiento, más de cinco acciones recibidas antes del descarte y sin archivo histórico dentro de002. Registrar límite de aceptación parcial FR-NIE-08 en `specs/002-niebla-ir-a/quickstart.md`. Dep.: T042. Requisitos: FR-NIE-08.
- [X] T044 [US1] Extender `src/orchestrator/bench.py` y correr_todo con bench_conocimiento/bench_ir_a conservando benchmarks existentes: semilla20261106, tamaños100/1000/10000, grado≤4, cadenas/mallas/empates, conocimiento parcial/completo y puertas estables/desactualizadas; Muestreo adaptativo por tamaño: 1000/100/10 consultas para100/1000/10000 salas, con100/10/1 calentamientos; contar y publicar cada muestra. Ajuste de método2026-11-09 documentado en research; el enunciado no fija cantidad de repeticiones. Separar consulta puntual/mapa completo/búsqueda y excluir generación/HTTP/render/drenaje del cálculo; mediana/p95/máximo, memoria, registros tocados, CPU/SO/Python/V/E/versiones. Usar ordenamiento propio para estadísticas; comparar índice vs lineal y heap vs cola lineal con resultados equivalentes. Dep.: T043. Requisitos: FR-NIE-19, FR-NIE-20.
- [X] T045 [US1] Ejecutar `python -m src.main --bench` y registrar datos sintéticos reproducibles en `DECISIONES.md`: límite≤5 ms sobre cada cálculo medido con máximo/fallos, sin afirmar referencia oficial; comprobar revelación de mismas vecinas sobre mapas crecientes por conteo de registros de salas/puertas consultados o modificados. Medir secuencias que crucen umbrales de expansión del índice, incluyendo tiempo y registros recorridos en rehash dentro del costo total amortizado; distinguir operaciones ordinarias de expansiones, sin excluir estas para afirmar SC-NIE-02. Si falla, optimizar solo002 y repetir cargas afectadas documentando cambios. Dep.: T044. Requisitos: FR-NIE-19, FR-NIE-20.

**Checkpoint US1**: comportamiento aislado y evidencia sintética disponibles; no certifica integración001, historia completa004 ni referencia oficial. No marcar tareas ejecutadas por haberlas generado.

## Fase 4: Integración, documentación y cierre

**Objetivo**: reunir evidencia real y declarar condiciones externas aún pendientes. Depende de T040–T045; las tareas bloqueadas permanecen pendientes sin impedir reportar avances ya comprobados.

- [ ] T046 Verificar entrega real de001 en `tests/test_sesion.py` y `tests/test_viaje.py`: costo/tiempo por movimiento, simetría/observación desde ambos extremos y empate de primer paso; retirar supuestos del falso en esta aceptación integrada, sin implementar cazadores ni duplicar fórmula. Registrar resultado o bloqueo en `specs/002-niebla-ir-a/quickstart.md`. Dep.: T002 y entrega externa001. Requisitos: FR-NIE-05, FR-NIE-11, FR-NIE-12.
- [ ] T047 Medir referencia offline oficial compatible con `src/orchestrator/bench.py` y registrar ID/versiones/semilla/V/E/máquina y máximo de cálculo en `DECISIONES.md`; verificar≤5 ms por paso y proporcionalidad de revelación. Mantener pendiente si no está disponible el paquete, sin sustituirlo por sintéticos para aceptación oficial. Dep.: T045,T046 y referencia externa. Requisitos: FR-NIE-19, FR-NIE-20.
- [X] T048 Consolidar `DECISIONES.md` con problema, alternativas, elección de índice/heap/núcleo propio, complejidad, mediciones reales y límites; justificar separación de rutas frente a001 y frontera de historia004. Enlazar evidencia sintética y, cuando exista, oficial, sin adjudicar trabajo§5.6 completo ni elección K a002. Dep.: T045; actualizar después de T047 si procede. Requisitos: FR-NIE-20.
- [X] T049 Ejecutar recorrido manual offline de `specs/002-niebla-ir-a/quickstart.md` en consola y Pygame y actualizar ayuda en `README.md`: mapa/viaje/cancelar, undo, guardar/cargar y cruce manual conservado. Usar fixtures para ramas que paquete_demo no contiene; registrar resultados/limitaciones, sin afirmar escenarios no recorridos. Dep.: T041,T042. Requisitos: FR-NIE-18, FR-NIE-21. Evidencia 2026-11-13 en quickstart y `docs/mediciones/002-t049-*`: consola fase A (demo real: rechazos, oleadas, viajes detenidos por daño de trampas, derrota por quemadura) y fase B (fixture limpia con todas las ramas: viaje, consultas conservan, carga inválida conserva, cancelación a mitad, antorcha+deshacer, guardar/cargar); vista headless a 1024×800 y 640×480 (mapa sin nombres de avistadas, Enter solo a exploradas, U y Escape cancelan, cruce manual por proximidad, pausa/guardar/cargar). README actualizado (v4, U, Escape, avistadas sin nombre).
- [X] T050 Ejecutar regresión `python -m pytest tests/ -q` con SDL dummy y sin CRIPTA_API_REAL; resolver regresiones propias y documentar resultado en `specs/002-niebla-ir-a/quickstart.md`, conservando restricciones y separación de capas. Dep.: T043,T046,T049. Requisitos: P2§2.5/6.3/7.1. Evidencia 2026-11-13 en quickstart (501 aprobadas/1 omitida; sin regresiones; T046/T049 siguen abiertas por su propio alcance).
- [X] T051 Revisar matriz FR/escenarios en `specs/002-niebla-ir-a/tasks.md` y registrar prompts/usos/resultados en `PROMPTS_LLM.md`; cerrar solo tareas verificadas y declarar pendientes de contratos, enunciado,001,004 o referencia. La entrega aislada de002 puede validarse con proveedores y colectores falsos, pero la aceptación completa de FR-NIE-08 espera la integración histórica real de T052. La aceptación completa de002 requiere T003 con contraste resuelto, T046,T047,T050,T052 y todas sus evidencias; no dar por terminada004. Dep.: T048,T049 y evidencias disponibles; cierre completo espera T047,T050,T052. Requisitos: P2§2.5/2.6. Revisión 2026-11-13 en la sección «T051» de este archivo: 18/21 FR con evidencia completa; FR-NIE-05/11/12 pendientes de T046 (entrega de001 de la persona A, fuera del alcance de B) y FR-NIE-19/20 de T047 (referencia oficial no publicada, evaluada como bloqueo externo sin resolución prevista); escenario 2 comparte la pendencia de T046; SC-NIE-01/02 sujetos a T047. Prompts 2026-11-09–2026-11-13 registrados en `PROMPTS_LLM.md`. La aceptación formal de002 queda incompleta por T046/T047, ambos bloqueos externos; no se da por terminada004.
- [X] T052 Verificar en `tests/test_deltas_conocimiento.py`, `tests/test_savegame.py` y `tests/test_sesion.py`, tras integrar004, el conocimiento histórico antes y después de entrada, revelación con antorcha y retroceso; comprobar reconstrucción correcta y conservación de la historia al guardar/cargar. Registrar evidencia o bloqueo en `specs/002-niebla-ir-a/quickstart.md`. El colector falso no cierra esta aceptación de FR-NIE-08; no implementar historia/checkpoints de004 dentro de002. Dep.: T043,T046,T050 y entrega externa004 compatible; mantener pendiente mientras no esté disponible. Requisitos: FR-NIE-08. Evidencia 2026-11-13 en quickstart: tres pruebas nuevas contra004 real (reconstrucción por frontera, concordancia deltas 002↔historia 004, validación/conservación v4). FR-NIE-08 histórico verificado; la dependencia T046 (001) sigue abierta para la aceptación completa de002.

## Dependencias y orden de ejecución

```text
T002,T003 → Fundamentos(T004–T007) → pruebas US1(T008–T016)
T001(K1 aprobado y enmendado) → T018; T001 completo → T024,T029,T030,T036,T038
Fundamentos → T017 → T018 → T019 → T020 → T021 → T022 → T023 → T024
Fundamentos + T010 + T002 → T025 ─────────→ T026 → T027 → T028
T024 + T028 + T001 → T029 → T030 → T031 → T032 / T033 → T034
T024 + T031 → T035 → T036 → T037
T030 + T014 → T038
T034 + T037 + T038 → T039 → T040 → T041 → T042 → T043 → T044 → T045
T045 → T046(entrega001) → T047(referencia oficial)
T045 → T048; T041,T042 → T049; T043,T046,T049 → T050
T043,T046,T050 + entrega004 → T052 → aceptación completa T051
```

Las «Dep.» en cada tarea precisan aristas adicionales. T018 depende de la aceptación y enmienda de K1 registradas en T001, no de completar T001. T032 se ejecuta antes de T039 como parte de la fase de interfaces; aunque no comparte archivos con T033, ambas consumen T031. No comenzar tareas con dependencias pendientes. Cambios compartidos de fachada/modelo/Sesión/vista se serializan, aun si pertenecen a subsistemas diferentes. T052 conserva el nuevo ID sin renumerar tareas anteriores; se ejecuta antes del cierre completo de T051, sin depender de ese cierre.

**Bloqueos externos**:

- T001 resuelto: aprobación directa del usuario y enmienda de K1/K2/K3/K5 registradas el 2026-11-08. No requiere contactar al compañero.
- T002/T046: coordinación y entrega de001, incluido estado físico de puertas recíprocas. No bloquea pruebas aisladas con falsos.
- T003 resuelto el2026-11-09: `docs/Cripta Parte II.md` leído y contrastado para002.
- T047: referencia oficial reproducible. Rendimiento sintético no la reemplaza.
- T052/FR-NIE-08:002 entrega estado/deltas/receptor comprobados con falso; archivo histórico y checkpoints se implementan en004. Su integración con conocimiento se verifica en T052 antes de aceptar completamente002; mientras004 falte, solo se declara entrega aislada/parcial.
- pytest disponible y suites ejecutadas: ver evidencia en quickstart; la ausencia al diseñar es solo histórica.

## Paralelismo posible dentro de US1

Los marcadores [P] describen oportunidades, no ordenan lanzar agentes.

| Momento | Tareas compatibles | Condición |
|---|---|---|
| Fundamentos | T004, T005, T006 | Archivos distintos; T007 espera T006. |
| Pruebas US1 | T008–T016 | Fundamentos completos; cada suite en archivo distinto. |
| Núcleo neutral | T025 junto a T017–T024 | Tras T010 y sus fundamentos; T025 no edita conocimiento/fachada/undo/Sesión. T026 espera ambas ramas. |
| Interfaces | T032 junto a T033 | Tras T031; consola y vista separadas. T034 sigue T033. |

Ejemplo para US1: tras T007, redactar T008 (conocimiento) y T010 (rutas) en paralelo; tras pruebas, desarrollar T025 mientras avanza conocimiento, y reunir ambas ramas en T026. No paralelizar T012/T041/T042/T046 entre sí: comparten tests/test_sesion.py.

## Estrategia incremental y criterios independientes

1. **Primer incremento verificable (parcial US1)**: fundamentos, T008,T012,T017–T021 tras aprobación K1; demostrar con proveedor falso y consumidor de prueba la sala inicial, avistadas, observación y consulta de conocimiento sin fugas ni mutaciones. No depende del viaje ni entrega todavía el comando público `mapa`, que llega con T030–T033. Cada tarea conserva su alcance completo y solo se marca al terminarlo.
2. **Reversión**: completar T022–T024 y T009; inicialización sin undo, entrada/antorcha reversibles, intervalos/exclusiones intactos y colector opcional.
3. **Viaje controlable**: unir núcleo, adaptador, contexto, C2 y Sesión; verificar T010–T012 sin UI/reloj real y luego controles de consola/Pygame.
4. **Persistencia/replay**: completar T035–T043 y demostrar igualdad lógica tras carga/reproducción sin continuación automática.
5. **Aceptación**: evidencia sintética, integración001 y referencia oficial más regresiones; mantener bloqueos pendientes. La entrega aislada no cierra FR-NIE-08: su conocimiento histórico requiere integración real con004 en T052. El primer incremento no es cumplimiento completo de002.

## Trazabilidad de requisitos

«Validación» señala tareas que crean/ejecutan evidencia futura, no resultados obtenidos. El contraste oficial sigue pendiente.

| Requisito | Implementación | Validación |
|---|---|---|
| FR-NIE-01 | T017,T019 | T008,T040 |
| FR-NIE-02 | T019 | T008,T040 |
| FR-NIE-03 | T017,T018,T021 | T008,T012,T040 |
| FR-NIE-04 | T017,T019,T031 | T008,T015,T041 |
| FR-NIE-05 | T018,T021 | T008,T011,T046 |
| FR-NIE-06 | T020,T023 | T008,T009,T040 |
| FR-NIE-07 | T026,T031,T033 | T008,T010,T015,T041 |
| FR-NIE-08 | T022–T024,T035–T037 | T009,T013,T042,T043; T052 verifica conocimiento histórico integrado con004 |
| FR-NIE-09 | T031–T033 | T012,T015,T016,T041 |
| FR-NIE-10 | T027,T030 | T011,T012,T041 |
| FR-NIE-11 | T025,T026 | T010,T040,T046 |
| FR-NIE-12 | T028–T030 | T011,T012,T041,T046 |
| FR-NIE-13 | T026,T027,T029 | T010,T011,T040 |
| FR-NIE-14 | T027–T030 | T011,T012,T040,T041 |
| FR-NIE-15 | T027,T029 | T011,T040 |
| FR-NIE-16 | T030,T038 | T014,T042 |
| FR-NIE-17 | T022,T029,T039 | T009,T011,T015,T040,T041 |
| FR-NIE-18 | T027,T031–T034 | T011,T015,T016,T041,T049 |
| FR-NIE-19 | T004,T017,T025,T026,T044 | T045,T047 |
| FR-NIE-20 | T044 | T045,T047,T048 |
| FR-NIE-21 | T027,T029,T030,T032,T034 | T011,T012,T015,T016,T041,T049 |

SC-NIE-01→T045/T047; SC-NIE-02→T044/T045/T047 (incluyendo expansiones en costo amortizado); SC-NIE-03→T040–T043. La parte histórica de FR-NIE-08 exige además T052.

## Trazabilidad de escenarios de aceptación

| Escenario de spec | Implementación | Validación |
|---|---|---|
| 1. Destino no explorado | T027,T030 | T011,T012,T041 |
| 2. Puerta recordada abierta pero cerrada | T021,T026,T029 | T008,T011,T040,T046 |
| 3. Entrada con dormidos | T028,T029 | T011,T040,T041 |
| 4. Entrada con antorcha | T019,T020 | T008,T040 |
| 5. Undo entrada con antorcha | T022,T023 | T009,T040 |
| 6. Pergamino durante viaje | T022,T029,T039 | T009,T011,T015,T041 |
| 7. Puertas remotas desconocidas/recordadas | T017,T020,T026 | T008,T010,T040 |
| 8. Enemigos vivos iniciales | T027,T030 | T011,T012,T041 |
| 9. Revelación inmediata al encender | T020 | T008,T040 |
| 10. Undo encendido | T022,T023 | T009,T040 |
| 11. Cancelar en5 tras2→5 sin avanzar a8 | T029,T030,T032,T034 | T011,T015,T016,T041,T049 |

## Resumen y siguiente paso

52 tareas en total: preparación3, fundamentos4, US1 38 y cierre7. Completadas T001–T045 y T048 (46); pendientes 6 (T046,T047,T049–T052). El corte de 2026-11-09 al final detalla evidencias y dependencias externas. Hay una sola historia, con pruebas independientes mediante falsos; [P] identifica 13 tareas (3 fundamentos,9 suites US1,1 núcleo). No equivale a13 ejecutores simultáneos.

Análisis de spec/plan/tasks realizado y cinco ajustes aceptados incorporados el 2026-11-08; la revisión documental no equivale a implementación ni aceptación funcional. La nota que sigue describe el estado inicial y fue supersedida por las secciones posteriores.

Implementación iniciada el 2026-11-08: T002–T007 completas, con42 pruebas nuevas
aprobadas y regresión total de298 aprobadas/1 omitida. Esta fotografía precede a
la aprobación directa de contratos y a la implementación posterior.

## Corte solicitado por el usuario — 2026-11-08

El usuario autorizó K1/K2/K3/K5 («apruebo todos los contratos»); T001 se cerró
con esa evidencia directa y enmienda en CONTRATOS.md. Luego solicitó «finish NOW»;
esa ejecución se reanudó después.

Trabajo adicional implementado y probado, con tareas todavía pendientes de
su alcance/validación completos: conocimiento incremental y deltas por registro,
Dijkstra neutral sobre conocimiento, inicialización/antorcha/observación local,
undo de conocimiento y reencendido, receptor opcional de cambios, control de viaje
con un movimiento/drenaje por avance, mapa DTO, comentario estricto de bitácora y
lectores/escritura v3 con carga candidata. No se marca una tarea completa por
implementar solo una parte ni se afirma aceptación integral de US1.

Validación: suite completa320 aprobadas/1 omitida; después del aislamiento de
estado candidato,38 pruebas focalizadas aprobadas. En ese corte faltaba conectar
consola/Pygame.

## Continuación de implementación — 2026-11-08

Consola conectada a mapa/viaje/cancelación con espera de150 ms y avance de un
paso por iteración; consultas mantienen el viaje. Pygame tiene panel M, selección
con flechas, inicio con Enter, cancelación con Escape, proyección local cacheada
por revisión, suspensión del movimiento con panel abierto y cancelación antes de
movimiento manual sostenido. README y quickstart actualizados. T032–T034 permanecen
sin marcar hasta completar pruebas de interfaz con lector/reloj inyectados, límites
temporales, cancelación/U y recorrido manual indicado por cada tarea.

Suite completa ejecutada en la integración inicial de interfaces: 320 aprobadas,
1 omitida. Después se hicieron retoques al cacheado del mapa, teclado sostenido y
presentación; no se repitió la suite. El resultado no implica escenarios completos
ni recorrido de consola/Pygame. Entregas001/004, benchmarks y referencia oficial
siguen pendientes.


## Verificación y cierre local — 2026-11-09

T008–T044 comprobadas con las suites offline y la revisión de las implementaciones
ya existentes. Se ampliaron pruebas de conocimiento inicial/observación remota,
receptor de cambios de inicio/acción/evento y aplicación bidireccional, viaje,
consola con reloj/lector inyectados, teclas sostenidas/U, temporizador, caché
visual, guardado v3, cargas candidatas fallidas, retroceso tras carga y ambos
reproductores del log. Los benchmarks se incorporan a `--bench` con estadísticas,
alternativas propias, matriz sintética y conteo explícito de rehash.

Correcciones encontradas: consola muestra salidas/costos/puertas y permite
inyectar sondeo/reloj; EOF/KeyboardInterrupt cancelan; el cruce automático recoloca
al personaje y activa `en_puerta`; la mochila y las teclas sin uso conservan el
viaje; la carga candidata clona la caché LRU para no compartir nodos activos.
El mapa gráfico muestra también las salidas, costos y memoria de puertas de la
sala seleccionada.

Las tareas T045–T052 siguen sujetas a resultados de medición, recorrido manual
e integración. La prueba con SDL dummy y los comandos de consola enviados por
stdin son recorridos automatizados, no una sesión manual humana. T046 espera
001 (los modelos vigentes aún no tienen costos ordinarios ni simetría física);
T047 espera paquete oficial; T052 espera004. T051 no puede cerrar aceptación
completa mientras falten esas entregas y el contraste con el enunciado P2.
T050 se ejecuta como regresión local, pero su cierre integrado espera T046/T049.


### Fuente oficial recibida durante la ejecución

2026-11-09: el usuario aportó `docs/Cripta Parte II.md`. Leído completo y
contrastado002; T003 ya satisface la condición de fuente íntegra. Se mantienen
las dependencias001/004 y referencia oficial, no el bloqueo por falta de enunciado.


### Resultado final de la ejecución — 2026-11-09

T045/T048 cerradas: `--bench` salida0, informe en
`docs/mediciones/002-niebla-2026-11-09.json` y resultados/límites en DECISIONES.md.
Se publican fallos del umbral sintético, no cumplimiento de5 ms: máximo heap
23,142/86,251/452,053 ms por tamaño. Tras reducir consultas redundantes se ejecutó
la matriz final completa con muestreo revisado documentado. La referencia oficial
permanece pendiente. Regresión final418 aprobadas/1 omitida en5,34 s; no cierra
T050 integrada porque sus dependencias T046/T049 siguen abiertas. Quedan seis
tareas: T046,T047,T049,T050,T051,T052. No se declara aceptación completa de002.


## T051 — revisión de matriz y cierre — 2026-11-13

Revisión de la matriz FR/escenarios contra el estado de casillas y las
evidencias registradas (T049 cerrada el mismo día; T050/T052 cerradas el
2026-11-13; T003 satisfecha con el enunciado íntegro recibido el 2026-11-09).

**Requisitos (21 FR).** Con evidencia offline completa: FR-NIE-01–04, 06–10,
13–18 y 21 (18 de 21). Con implementación cerrada pero aceptación integrada
pendiente: FR-NIE-05, FR-NIE-11 y FR-NIE-12 — su validación incluye T046
(entrega real de001: costos/tiempos ponderados, simetría y observación de
puertas desde ambos extremos); los falsos cubren el diseño, no la aceptación.
Con evidencia sintética disponible y aceptación oficial pendiente:
FR-NIE-19 y FR-NIE-20 — T045/T048 midieron con índice/heap propios (mediana
2,691 ms en malla de100; máximos 23,142/86,251/452,053 ms y 581/1000/100
consultas sobre5 ms en las cargas sintéticas más duras: no se acredita el
umbral) y la proporcionalidad de revelación se verificó con conteo constante
y expansiones incluidas; T047 (referencia oficial) no puede cerrarse sin el
paquete del enunciado §6.1.

**Escenarios (11).** Validados por pruebas y/o recorridos: 1, 3–11
(escenario 11 con T049 incluida). El escenario 2 (puerta recordada abierta
pero cerrada en realidad) comparte la pendencia de T046.

**Criterios de sistema.** SC-NIE-01 y SC-NIE-02 quedan sujetos a T047;
SC-NIE-03 cubierta por T040–T043 con la parte histórica verificada por T052
contra004 real.

**Pendientes declaradas.** T046: bloqueo externo — la entrega de001
(terreno-cazador) pertenece a la persona A según la división del trabajo del
proyecto; la persona B (002) solo la consume y 001 aún no tiene plan, tasks
ni implementación en el repositorio. T047: bloqueo externo sin resolución
prevista — la cripta de referencia del enunciado §6.1 no ha sido publicada y
el equipo la evalúa como no disponible (evaluación 2026-11-13, por confirmar
con el docente); la tarea misma ordena mantenerla pendiente sin sustitutos
sintéticos. **La aceptación formal completa de002 queda declarada
incompleta** por T046/T047, ambos bloqueos externos al alcance de B; todo lo
verificable sin esas entregas está cerrado y evidenciado. No se da por
terminada004 ni se adjudica a002 el trabajo §5.6 completo ni la elección de K.
