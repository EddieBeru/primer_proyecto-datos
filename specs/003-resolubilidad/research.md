# Investigación: resolubilidad003

Fecha: 2026-11-16. Fuentes primarias locales: [spec](spec.md), [constitución](../../.specify/memory/constitution.md), [contratos y enmiendas](../../CONTRATOS.md), [001](../001-terreno-cazador/spec.md), código de `src/models/conocimiento.py`, `src/models/rooms.py`, `src/estructuras/tabla_indice.py`, `src/controller1/endpoints.py`, `src/controller1/session.py`, `src/orchestrator/sesion.py` y `src/main.py`. No fue necesario consultar documentación externa ni contactar el servicio.

## D01 — Modelo único del esqueleto

**Cubre:** FR-RES-01/02/03/11/12; FR-CAZ-01/10.

**Decisión:** ampliar el modelo neutral existente `DatosSala`/`DatosSalida` en `src/models/conocimiento.py`, consumido también por002, con llave y estado inicial de puerta. Añadir `costo=100` al DTO de transporte `Exit` en `src/models/rooms.py`.001 y003 comparten esa representación, identidad física y constructor;003 no crea un segundo esqueleto ni un segundo índice de salas. Los costos se conservan pero no se usan como prioridad de verificación.

**Justificación:** `DatosSalida` ya contiene dirección, destino, costo y `puerta_id`, pero no llave ni estado inicial. `Exit` aún pierde `costo` al leer JSON. `preparar_metadatos` itera por cubetas, por lo que debe conservar además el orden original de páginas/salas para reportes. El plano de transporte puede usar JSON permitido, pero el cálculo usa índices propios.

**Alternativas:** modelo exclusivo003 descartado por duplicación y discrepancias con001; usar el estado vivo de002 descartado por mezclar conocimiento y plano completo. La simetría de costos y puertas recíprocas se valida en el constructor compartido, sin inventar inversas.

## D02 — Propagación incremental y evidencia acotada

**Cubre:** FR-RES-01/02/03/04/05/06/12.

**Decisión:** representar hechos monotónicos `alcanzable(sala)` y `obtenida(llave)`, y reglas de tamaño constante: sala origen y, si está cerrada, llave permiten sala destino; sala de ubicación permite obtener llave. Cada hecho pasa de falso a verdadero una sola vez. Descubrir una sala solo la marca y encola: no dispara sus salidas. Al atenderla se recogen primero sus llaves, después se habilitan sus reglas salientes N,S,E,O; pendientes se enlazan al identificarlas, no al compilar por orden fuente. Suscriptores por hecho y contadores de premisas pendientes permiten disparar cada regla una sola vez. No recalcular alcanzabilidad al obtener una llave.

**Justificación:** número de reglas/incidencias O(S+E+K+L), siendo L las ubicaciones. El esqueleto se ingiere una sola vez para construir el modelo compartido y sus evidencias; después solo se procesan activaciones incrementales y resúmenes derivados. No hay barrido del esqueleto después de cada llave. El reporte usa las mismas marcas y evidencias, con reducción global lineal de su residuo, no consultas de rutas por llave.

**Alternativas:** repetir búsqueda por llave O(K(S+E)) solo como referencia en `--bench`; grafo completo llave→llave rechazado porque puede crecer cuadráticamente y pierde alternativas.

## D03 — Estructuras propias y mediciones

**Cubre:** FR-RES-05/07/12/13.

**Decisión:** FIFO propia encapsulada sobre arreglo de ordinales y cursor de cabeza, arreglos de marcas/contadores/padres, listas de adyacencia con enlaces por ordinal, pila iterativa propia y `TablaIndice` neutral para id de sala→ordinal. Para llaves textuales, ampliar `TablaIndice` neutral con claves str y hash propio FNV-1a de64 bits sobre bytes UTF8, con máscara en cada paso y comparación del texto completo en cada colisión. Preservar comportamiento de claves enteras/extremos; no usar el hash de Python como identidad ni su orden de cubetas como desempate. Preservar IDs originales para presentación. El hash no es la identidad: dos textos de igual hash siguen siendo llaves distintas.

**Evidencia:** [script reproducible](../../docs/mediciones/003-estructuras-plan.py) y [muestras/entorno](../../docs/mediciones/003-estructuras-plan.json), dos calentamientos y siete repeticiones. Última ejecución: FIFO32000 arreglo+cursor2,995 ms, quitar frente83,017 ms y enlazada9,459 ms. Índice propio entero4000:19,806 ms frente a búsqueda lineal174,224 ms. Texto16 caracteres,4000 IDs: hash textual FNV47,769 ms frente a codificación entera46,665 ms y búsqueda lineal169,080 ms. Texto256 caracteres,4000 IDs: FNV535,167 ms frente a codificación392,360 ms. FNV no fue más rápido en estas cargas: se elige por su procesamiento lineal por byte con acumulador acotado, no por una ventaja temporal inexistente. Los IDs largos muestran que no cabe certificar200 ms para entradas arbitrarias. Estas son mediciones estructurales, no del verificador ni de la mayor cripta publicada.

**Alternativas:** cola enlazada propia válida pero más costosa en esa carga; `pop(0)` descartado por desplazamientos; búsqueda lineal repetida por id descartada. `heapq`, `deque`, `set`, `frozenset`, diccionarios como índices, `sorted` y `list.sort` no se admiten en la funcionalidad nueva. No importar estructuras de C1 a C2. Convertir ids a enteros con `int.from_bytes` fue una alternativa preliminar medida, descartada: `_hash_entero` desplaza repetidamente enteros de longitud decreciente y no permite justificar costo lineal en bytes arbitrarios. La ampliación textual procesa cada byte una vez; la tabla existente da costo esperado amortizado, no garantía de peor caso frente a colisiones adversarias; registrar distribución/cadenas en las mediciones completas.

## D04 — Determinismo

**Cubre:** FR-RES-04/05/07/15.

**Decisión:** seguir exactamente el orden de descubrimiento aprobado: FIFO de salas; llaves antes que salidas de cada sala; llaves por orden de consulta; salidas N,S,E,O; puertas pendientes habilitadas por una misma llave por su ordinal de primera identificación. Despertar puertas al registrar la llave, antes de continuar el trabajo de esa sala; los destinos se añaden al final de la FIFO. Repeticiones de un hecho no generan nuevos registros. Los ordinales fuente de salas conservan página y posición original, independientemente de la tabla hash. Misma entrada ordenada implica mismo resultado; no se promete invariancia a reordenamientos de entrada.

**Alternativas:** menor id global rechazado porque el usuario aprobó descubrimiento y porque no es necesario mantener una prioridad. No ordenar globalmente todos los ciclos.

## D05 — Ciclos con alternativas: conflicto resuelto con el usuario

**Cubre:** FR-RES-06/07/12/15.

**Decisión:** conservar el residuo de reglas AND/OR, no proyectar dependencias como requisitos individuales inevitables. El usuario aprobó «pues hazlo» después de recomendar un ciclo de alternativas bloqueadas acompañado de las demás alternativas bloqueadas. FR-RES-07/15 y escenario13 se corrigieron con esa autorización, sin nombres de implementación en el spec.

**Justificación:** A accesible con B O C, B y C accesibles con A: ninguna llave es obtenible, pero B no es requisito inevitable para A. La semántica anterior «obtener A exige B» era falsa al mostrar A→B→A. Ahora la flecha significa una alternativa bloqueada. Se conserva explícitamente la evidencia del resto de alternativas; un circuito aislado no demuestra por sí solo imposibilidad.

**Diseño:** al terminar la propagación, conclusiones falsas apuntan a sus reglas alternativas; cada regla pendiente apunta a sus premisas falsas, con etiquetas de puerta, dirección y ubicación. Calcular componentes fuertemente conexas en esa evidencia mediante Tarjan iterativo propio (índices, lowlink, pila y marcas densas). Elegir un circuito que incluya una obtención de llave y una puerta cerrada que requiere una llave no obtenida; ignorar ciclos de salas sin llaves. Dentro del primer componente elegible por el orden de sus llaves, buscar desde su primera llave el primer retorno a ella con orden estable de dependencias y pila iterativa; conservar testigo. Presentar las llaves del circuito y las puertas/rutas que las conectan, junto con todas las alternativas bloqueadas de esas llaves, sin desplegar por separado todos los caminos posibles. La elegibilidad se determina linealmente examinando incidencias internas, sin un ensayo por llave/componente. Los detalles del criterio de selección están en plan.md.

**Límite:** hay una reducción global O(S+E+K+L) de las evidencias ya recogidas, con visitas a esas evidencias; no es una nueva exploración del esqueleto ni una búsqueda por llave. No afirmar que Tarjan por sí solo prueba dependencias inevitables. Pruebas de alternativas, regiones desconectadas y ciclos sin llaves son obligatorias.

## D06 — Endpoint y persistencia

**Cubre:** FR-RES-01/02/11/14.

**Decisión:** propuesta `GET /criptas/{id}/llaves`, resuelta como `/llaves` de la cripta, con id/versión y ubicaciones completas, incluidos enemigos y salas iniciales; consultar por C1 con el budget de la preparación. El formato exacto se propone en contratos; no se presenta como respuesta comprobada del servidor. Caché independiente del catálogo, clave(id,versión), orden intacto, publicación atómica y validación antes de usar. El404 del endpoint es error de consulta, no una lista vacía.

**Justificación:** no descargar contenidos o catálogo para deducir llaves; cada intento/reintento y validación remota cuenta en el presupuesto vigente. Offline cero HTTP. No cambiar guardado v4 por persistir un insumo versionado externo.

**Alternativas:** extraer `suelta` descargando enemigos descartado por solicitudes y por usar posición posterior. Consulta sin budget descartada.

## D07 — Preverificación, CLI y vista

**Cubre:** FR-RES-08/09/10/14/15.

**Decisión:** preparar insumos y verificar antes de crear estado, catálogo de juego, enemigos, bitácora o vista en modo `--verificar`. Sesión expone resultado/DTO también cuando inicio bloqueado; solo crea la partida si es resoluble o el usuario forzó una imposibilidad demostrada. `--forzar` no evita errores de datos. Cargar/replay conservan su flujo existente: la verificación nueva no invalida retroactivamente partidas forzadas ni consume solicitudes adicionales al reproducirlas.

**Justificación:** hoy `Sesion.iniciar` carga catálogo antes del plano y crea estado inmediatamente. Es necesario separar preparación y confirmación de inicio, manteniendo el budget y plano preparados sin volver a descargarlos. `main` debe despachar `--verificar` antes de importar Pygame. La interfaz solo consume Sesión/DTO, con texto compartido y scroll.

**Auditoría:** existen `set` heredados en caché, ProveedorSesion, enemigos y vista; no reutilizarlos como auxiliares de003. Preverificación no construye esas dependencias. En puntos de integración tocados, sustituir auxiliares de reporte por marcas/TablaIndice; mantener una comprobación transitiva del flujo de verificación sin prohibidos. No declarar que todo el repositorio actual cumple la prohibición ni rehacer funcionalidades ajenas sin necesidad.

## D08 — Aceptación y límites

**Cubre:** FR-RES-01–15.

**Decisión:** validación offline primero, oráculo de barridos repetidos solo en pruebas/benchmark, casos de Apéndice B y contraprueba AND/OR; contadores estructurales además de tiempos. Meta200 ms sobre la mayor cripta publicada, incluyendo preparación local, reducción residual, orden y texto, excluyendo red/renderizado. Sin paquete oficial no certificar esa meta.

**Justificación:** las cifras de microbenchmarks son evidencia parcial para elegir estructuras; no permiten declarar rendimiento del producto. Se registra una decisión provisional de diseño con mediciones y condiciones de revisión en DECISIONES.md.

**Estado de investigación:** decisiones resueltas. Formatos/interfaces son propuestas reviewables sujetas al procedimiento de contratos antes de implementación, no afirmaciones sobre un servidor observado. No se han ejecutado pruebas del verificador aún inexistente.
