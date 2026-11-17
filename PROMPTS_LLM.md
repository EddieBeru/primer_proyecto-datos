# Bitácora de prompts del proyecto — Estructura de Datos — Cripta

**Estudiantes:** Luis Quesada Montero, Eddie Bermudez Ureña.
**Profesor:** Jose Pablo Calvo Suarez.
**Fecha de entrega:** 18 de octubre de 2026.

Registro del uso de modelos de lenguaje (LLM) durante el proyecto, según §10.3 del enunciado. Cada entrada indica fecha aproximada, modelo utilizado, el prompt enviado y una frase con el uso que se le dio a la respuesta. Los prompts se transcriben tal como se enviaron o, cuando la sesión fue conversacional o extensa, condensados conservando lo esencial; las paráfrasis se marcan como tales. No se incluyen respuestas completas, credenciales ni datos ajenos al proyecto. El código y el texto generados con apoyo de un LLM son responsabilidad del grupo.

| Fecha | Modelo | Prompt | Uso |
|---|---|---|---|
| 2026-10 (inicio) | Muse Spark | "Te adjunto el enunciado; quiero una distribución asincrónica para trabajar con mi compañero, que ambos toquemos los conceptos importantes del proyecto. Ayúdanos con lo básico para inicializar, qué partes merecen investigación propia de estructuras de datos y qué frameworks, tecnologías o estándares conviene usar." | Plan de división entre controladores (C1/C2) y temas de investigación de estructuras de datos |
| 2026-10-11 | Muse Spark 1.3 | "¿Cómo hago para que mi función make_request me devuelva los datos ya convertidos a la clase que yo le pida y, si la API devuelve un error, me devuelva una clase de error en vez de romperse? Solo explícame la idea, sin código todavía." | Diseño de la conversión de respuestas y de los errores tipados en el cliente HTTP |
| 2026-10-11 | Muse Spark 1.3 | "¿Cómo le agrego a esa misma función la opción de pasarle None para que me devuelva el JSON crudo?" | Modo de respuesta cruda del cliente |
| 2026-10-11 | Muse Spark 1.3 | "¿Me lo puedes explicar más simple y qué hace cada parte?" / "Recuérdame cuál es el plan actualizado para terminar el make_request con lo que ya tenemos." | Aclarar el diseño parte por parte y cerrar el plan del cliente |
| 2026-10-11 | Muse Spark 1.3 | "Hazme solo el from_dict de la clase Trap: el atributo se llama dano pero se lee del JSON donde dice daño. No hagas nada más." / "Ahora hazle el from_dict al resto de mis modelos igual como hiciste con Trap." | Plantilla de from_dict con traducción daño→dano y su réplica en todos los modelos |
| 2026-10-15 | Muse Spark (opencode) | "según documentación e implementación, cómo se ve el controlador 1 y 2?" | Mapear C1/C2 docs vs código |
| 2026-10-15 | Muse Spark (opencode) | "a que te refieres con formulas profe?" | Listar fórmulas pendientes (daño, intervalo, rastro, puntaje) |
| 2026-10-15 | Muse Spark (opencode) | Doc oficial PDF del profe + "revisa rápidamente y dime si lo confirma" | Confirmar fórmulas y deltas contra implementación |
| 2026-10-15 | Muse Spark (opencode) | "resuelve todo eso" / "hazlo y luego explicas qué ocurrió" | Alineación completa a doc oficial (motor + C1 + pruebas + docs) |
| 2026-10-15 | Muse Spark (opencode) | "no estaba al día con la rama, revisa de nuevo" | Reinspeccionar rama mergeada y corregir resumen C1/C2 |
| 2026-10-15 | Muse Spark (opencode) | "si no me equivoco, hace falta un tercer controlador orquestador?" | Confirmar hueco de orquestación y plan Sesión/loop |
| 2026-10-15 | Muse Spark (opencode) | "aprovechando que hay bitacora de prompts, agrega lo más relevante de lo que solicite yo. Con eso dicho, implementame el orquestador porfa" | Registrar prompts faltantes e implementar orquestador Sesión |
| 2026-10-18 | deepseek-v4.1-flash-free (opencode) | "Quiero hacer cambios en el comportamiento y movimiento del personaje; recuerda documentar mis prompts en el documento de bitacora. además, recuerda checar los archivos de documentación para mantenerse a raya según las reglas de los enunciados y acuerdos pasados. espera instrucciones posteriores" | Revisar docs/contratos vigentes y dejar lista la bitácora para la tanda del personaje |
| 2026-10-18 | deepseek-v4.1-flash-free (opencode) | "el movimiento del personaje debe estar normalizado para evitar que un movimiento diagonal sea más rápido que uno recto." | Normalizar movimiento diagonal (`src/view/app.py`) + prueba + DECISIONES 38 |
| 2026-10-18 | deepseek-v4.1-flash-free (opencode) | "me gustaría que hubiera más animaciones o indicios: que se coloree de rojo y haga un pequeño shake al recibir daño, y una estela tipo trayectoria de espada al atacar con esta, o un movimiento rápido si ataca sin espada." / "me encantaría si la estela fuera totalmente blanca" | Feedback visual de combate (tinte+shake, estela o embestida) y estela a blanco puro; DECISIONES 39 |
| 2026-10-18 | deepseek-v4.1-flash-free (opencode) | (paráfrasis) al mirar arriba/abajo tras caminar a la izquierda el personaje se voltea a la derecha, y el paso pega un brinco al cambiar de dirección. / "si esos cambios se pueden aplicar en arma y escudo, hazlo: podría crear un código más estable que el parche que apliqué antes" / "me gustaría que la animación de ataque sin espada se mostrara también con espada, además del flash" | Espejo persistente + paso suavizado, espada/escudo alineados con caché por lado y embestida siempre visible; pruebas y DECISIONES 40-41 |
| 2026-10-18 | deepseek-v4.1-flash-free (opencode) | "quiero que el nuevo sfx suene cada que empiece la partida como un guiño a la empresa de la cual se inspiró los visuales del juego." / "el icono de la app aún es un asset por defecto: ¿podrías hacerlo el frame de paso del personaje?" | Jingle al iniciar partida e icono de ventana con el prota; pruebas y DECISIONES 42-43 |
| 2026-10-18 | deepseek-v4.1-flash-free (opencode) | "el volumen del SFX está muy alto, déjalo a la mitad" / "el volumen del efecto de sonido está todavía muy alto" | Volumen final 0.1 con `set_volume` en cada reproducción; DECISIONES 62 |
| 2026-10-18 | deepseek-v4.1-flash-free (opencode) | "pregunta; cada que entro a una sala que contenga pinchos, recibo daño aunque no esté ni cerca. bug, diseño o mandatorio?" + "implementa así" | Chispazo en la trampa disparada + aviso «¡Trampa al entrar!»; pruebas y DECISIONES 44 |
| 2026-10-18 | deepseek-v4.1-flash-free (opencode) | "viene un gran rework de la interfaz gráfica: mejorar los menús de inicio (elegir cripta en online) y el de victoria/derrota: más user-friendly, más gráficos para entendimiento instantáneo, mejor distribución y lógica gráfica." | Rework de menús y pantalla final; pruebas y DECISIONES 45 |
| 2026-10-18 | deepseek-v4.1-flash-free (opencode) | "deberíamos revisar el comportamiento de los enemigos: qué dicen las indicaciones y cómo se comportan ahora? me parece que están muy sosos…" + "a y b porfa" | Regeneración de catálogo para enemigos (§2.10) y embestida enemiga visible; pruebas y DECISIONES 46-47 |
| 2026-10-18 | deepseek-v4.1-flash-free (opencode) | "al abrir el juego desde el comando sin más (online), no debería mostrar el menú principal?" | Arranque en menú principal; prueba y nota en DECISIONES 45 |
| 2026-10-18 | deepseek-v4.1-flash-free (opencode) | "en los menús, el sprite del prota se renderiza en una resolución muy pequeña aunque el canvas permita más píxeles" / "esta nueva implementación ahora tiene antialiasing. eso no" | Prota de menús desde el PNG nativo con escala nearest por defecto; prueba y DECISIONES 48 |
| 2026-10-18 | deepseek-v4.1-flash-free (opencode) | "la bitacora renderizada es innecesaria [...] canvas centrado [...] contadores y objetos abajo, ratio 4:1" / "agregale un padding al canvas y una fila inferior con los controles importantes en todo momento" | HUD rediseñado: canvas centrado, banda de contadores + mochila y fila de controles; DECISIONES 49 |
| 2026-10-18 | deepseek-v4.1-flash-free (opencode) | "todavía más padding. implementar los assets de Pizza Box: Box es el fondo del canvas, los Lids son la animación de la tapa; Stage 1 en el menú de inicio, 6 es el frame final, y ahí adentro podría ir el título" | Caja de fondo del canvas y menú con la tapa abriéndose; 3 pruebas y DECISIONES 50 |
| 2026-10-18 | deepseek-v4.1-flash-free (opencode) | "el resto de menús deberían mostrar la caja de pizza para que el zoom tenga sentido [...] que el canvas del juego se ajuste a la zona libre del sprite: posición 110px/110px y expansión 290px/290px, centrado si no es cuadrado" | `zona_caja`/`rect_caja` inversos y caja tenue en todos los menús; prueba y DECISIONES 51 |
| 2026-10-18 | deepseek-v4.1-flash-free (opencode) | "el menú de elegir cripta debería seguir el mismo layout que el principal: caja de pizza arriba y opciones abajo; adapta eso junto con el resto de menús." / "ocupamos más tamaño de ventana para que el canvas de juego no sea tan apretado" | Menús unificados con `_caja_menu` y ventana 1024×800; DECISIONES 52 |
| 2026-10-18 | deepseek-v4.1-flash-free (opencode) | "durante el zoom hay 2 versiones de la caja renderizándose a la vez: oculta la caja de juego durante la animación e intercambia las versiones cuando terminen." / "los botones de todos los menús deberían ser interactuables por el mouse" | Solo la caja interpolada durante el zoom + hotspots de mouse en menús; DECISIONES 52-53 |
| 2026-10-18 | deepseek-v4.1-flash-free (opencode) | (paráfrasis) auditar el proyecto contra el enunciado y la rúbrica, listar brechas y arreglarlas por bloques sin tocar `deshacer.py` ni el flujo del pergamino | Auditoría §2–§11 y bloques 2–9 (almacén, buffer, agenda, ordenamientos, bench); DECISIONES 54–61 y parte A del documento §8 |
| 2026-10-18 | deepseek-v4.1-flash-free (opencode) | (paráfrasis) muchos objetos del catálogo salen sin sprite (magenta); clasifícalos por familia de nombre | Grupos `_CLAVES_*` en `sprites.py` + prueba; DECISIONES 62 |
| 2026-10-18 | deepseek-v4.1-flash-free (opencode) | "documenta las decisiones en el formato que pide el enunciado (problema/alternativas/decisión/complejidad/bench/límites)" | Parte A del Documento de Decisiones por §4.1–§4.11 con números de `--bench` |
| 2026-10-18 | deepseek-v4.1-flash-free (opencode) | "resuélveme el conflicto" | Resolución del merge con `origin/main` (agenda indexada con guarda seq=-1, ranuras de equipo, kwargs de mochila + rebobina) |
| 2026-10-18 | deepseek-v4.1-flash-free (opencode) | "qué le falta al pergamino? dice que no se puede usar 'así'" | Ruta del pergamino a `deshacer()` en `Fachada.usar`; prueba y DECISIONES 65 |
| 2026-10-18 | deepseek-v4.1-flash-free (opencode) | "haz que todos los enemigos compartan el mismo sprite. asegúrate de que toda poción comparta el mismo, igual que las curaciones como el antídoto" | Sprite único de enemigo y frasco único de consumibles en `sprites.py`; pruebas y DECISIONES 62 |
| 2026-10-18 | deepseek-v4.1-flash-free (opencode) | (paráfrasis) quitar los `TODO`/notas pendientes que quedaban en el controlador 2 | Limpieza de 26 marcadores conservando los invariantes reales como comentarios |
| 2026-10-18 | deepseek-v4.1-flash-free (opencode) | "crea una bitácora más seria integrando la planificación inicial y la conversación sobre make_request, y normaliza el formato para que los prompts queden concisos y directos" | Reescritura de este documento |


## Parte 2 — Codex y GitHub Spec Kit

Fechas aproximadas de la sesión; los textos extensos se resumen como paráfrasis.
El modelo se identifica como Codex sin atribuir una variante no confirmada.
Los resultados indicados son documentales, sin ejecución de pruebas del juego.

| Fecha | Modelo | Prompt | Uso |
| --- | --- | --- | --- |
| 2026-11-04 | Codex | (paráfrasis) Fijar @v1.0.0, registrar que parte 2 usará Codex y GitHub Spec Kit y versionar su configuración. | README, etiqueta local e incorporación de archivos de Spec Kit. |
| 2026-11-04 | Codex | (paráfrasis) Generar un prompt y luego usar $speckit-constitution para redactar la constitución de CRIPTA en español, con siete principios y gobernanza, modificando solo la constitución. | Constitución inicial 1.0.0; registro diferido por el alcance autorizado entonces. |
| 2026-11-05 | Codex | (paráfrasis) Capacidad terreno y cazador: costos de tránsito, persecución por costo mínimo, desempate por id, equivalencia observable y límites de rendimiento; sin detalles de implementación. | Entrada conservada en specs/001-terreno-cazador/spec.md. |
| 2026-11-05 | Codex | (paráfrasis) Capacidad niebla de guerra e ir a: conocimiento y memoria de puertas, antorcha, viaje paso a paso, retroceso y rendimiento; sin detalles de implementación. | Entrada conservada en specs/002-niebla-ir-a/spec.md. |
| 2026-11-05 | Codex | (paráfrasis) Capacidad verificación de resolubilidad: llaves obtenibles, diagnóstico determinista, --forzar, --verificar y rendimiento; sin detalles de implementación. | Entrada conservada en specs/003-resolubilidad/spec.md. |
| 2026-11-05 | Codex | «lee CRIPTA Parte II para más contexto» / (paráfrasis) Verificar las carpetas y la integración con Spec Kit / «ajustalos para que coinciden». | Conversión separada de las cuatro capacidades de la guía a specs/001–004, con plantilla resuelta, requisitos identificados, escenarios, supuestos y checklists. Línea de tiempo se tomó del bloque 004 de la guía. Actualización del índice y README. |
| 2026-11-05 | Codex | (paráfrasis) Preparar y ejecutar el prompt de $speckit-clarify para 002 según el contexto actual, revisando fuentes y supuestos antes de planificar. | Inicio de revisión documental de 002 con selección explícita de capacidad; sesión de preguntas en curso, sin implementación ni mediciones. |
| 2026-11-05 | Codex | «A» (pregunta 1 de clarify 002: antorcha y puertas remotas). | Aclaración integrada en 002: revelación de nombre, salidas y costos, sin observación remota de puertas; estado desconocido excluido de «ir a». |
| 2026-11-06 | Codex | «A» (pregunta 2 de clarify 002: iniciar «ir a» con enemigos vivos en la sala actual). | FR-NIE-14 y escenario de aceptación actualizados: el viaje no inicia, explica el motivo y no consume tiempo; el movimiento manual sigue disponible. |
| 2026-11-06 | Codex | «A» (pregunta 3 de clarify 002: revelación al encender la antorcha). | FR-NIE-06 y FR-NIE-08 precisados, con escenarios de revelación inmediata y reversión del conocimiento al deshacer el encendido. |
| 2026-11-06 | Codex | (paráfrasis) Explicar «ir a» y su cancelación frente al cruce por proximidad actual; «A» (pregunta 4 de clarify 002: cancelación voluntaria entre pasos). | Revisión de la vista y del flujo Sesión→motor; FR-NIE-21 y escenario de cancelación añadidos. Sesión cerrada con cuatro respuestas integradas; checklist revalidado, sin código ni mediciones y con contraste del enunciado íntegro de P2 pendiente. |
| 2026-11-06 | Codex | `$speckit-plan` con `SPECIFY_FEATURE_DIRECTORY=specs/002-niebla-ir-a` y las instrucciones de la habilidad. | Investigación local con dos agentes de lectura y generación de plan, research, data-model, propuesta contracts/interfaces y quickstart; revisión constitucional y consistencia documental. Sin código, tareas, commits ni benchmarks. pytest ausente en .venv; aceptación de contratos por el compañero e integración de 001/004 pendientes, sin afirmar contraste con enunciado íntegro P2. |
| 2026-11-06 | Codex | (paráfrasis) Preparar prompt-plan y ejecutar `$speckit-tasks` para 002, con selección explícita `SPECIFY_FEATURE_DIRECTORY=specs/002-niebla-ir-a`, una sola US1, coordinación de contratos/001/004, pruebas offline, mediciones y trazabilidad, sin implementar producto ni versionar. | Generado tasks.md con 51 tareas pendientes (38 US1, 13 con oportunidad de paralelismo), matriz de 21 requisitos y 11 escenarios, dependencias y primer incremento parcial. setup_tasks resolvió plantilla e insumos; validación documental de formato, IDs, dependencias explícitas, referencias/enlaces y espacios; extensions.yml ausente antes/después, sin hooks. Sin pruebas del juego, instalaciones, benchmarks, cambios de contratos, commits ni push. Aceptación del compañero, entrega001, historia completa004, contraste con enunciado íntegro P2 y referencia oficial permanecen como condiciones explícitas; siguiente paso speckit-analyze. |
| 2026-11-08 | Codex | `$speckit-analyze SPECIFY_FEATURE_DIRECTORY=specs/002-niebla-ir-a` | Análisis de solo lectura de spec/plan/tasks y constitución: 24 requisitos/criterios con tareas asociadas, 51 tareas pendientes y 11 escenarios trazados; dos hallazgos altos y tres medios, ninguno crítico. Señaladas garantía amortizada de revelación, aceptación histórica con004, excepciones de cancelación, complejidad de proyección y dependencia de aprobación K1. Sin pruebas del juego ni benchmarks; registro diferido hasta autorizar edición. |
| 2026-11-08 | Codex | «propon» / «acepto» (propuesta y aceptación de cinco ajustes documentales tras analyze 002) | Actualizados spec, plan, tasks, research, data-model, propuesta de interfaces y quickstart: revelación esperada amortizada incluyendo expansiones; T052 de aceptación histórica integrada con004 y distinción de entrega aislada; consultas/carga fallida preservan viaje; complejidad de proyección ordenada; aprobación K1 independiente para T018. Quedan 52 tareas pendientes, sin renumerar ni implementar. Validación documental de formato, referencias, dependencias, enlaces y espacios; sin pruebas del producto, mediciones, cambios de CONTRATOS.md, commits ni push. La aceptación del compañero y el contraste oficial P2 siguen pendientes. |
| 2026-11-08 | Codex | `$speckit-implement SPECIFY_FEATURE_DIRECTORY=specs/002-niebla-ir-a` / «no me hiciste la pregunta» | Checklist16/16 completo y sin hooks previos. Completadas T002–T007: registro de integración/fuentes pendientes, instalación local de pytest9.2.0 tras solicitud de red, índice hash y heap propios, DTO inmutables y fixtures offline instrumentadas; actualizado gitignore de Python. Pruebas focalizadas42 aprobadas; suite completa298 aprobadas/1 omitida con SDL dummy y sin CRIPTA_API_REAL; sin benchmarks ni aceptación funcional de US1. Registradas decisiones y evidencia; T001 sigue pendiente, sin cambios de contratos ni formatos. La pregunta sobre aceptación del compañero se envió por formulario y el usuario indicó que no la vio; se presenta directamente en la conversación. Sin commits ni push. |
| 2026-11-08 | Codex | «apruebo todos los contratos» / «hurry up» / «finish NOW» | Registrada autorización directa del usuario y enmienda K1/K2/K3/K5; T001 completa. Implementación adicional parcial de conocimiento/deltas, Dijkstra, antorcha/undo, receptor, viaje por pasos, mapa DTO, comentario de bitácora y v3/carga candidata. Suite completa320 aprobadas/1 omitida; ajuste posterior de aislamiento candidato validado con38 pruebas focalizadas. Corte solicitado por el usuario: faltan interfaces consola/Pygame, ampliar persistencia/replay, benchmarks y aceptación integrada001/004/referencia. Sin declarar completo002, commits ni push. |
| 2026-11-08 | Codex | «que tal si empezamos el numero 4?» / respuestas a `$speckit-clarify` sobre conteo y renumeración de acciones, compatibilidad de guardados y tiempos repetidos | Aclarar y planificar `004-linea-de-tiempo`; actualizar spec, research, data model, contratos propuestos y validación. La revisión del modelo no sustituye al equipo ni al enunciado oficial P2. |
| 2026-11-08 | Codex | «ajuta los documentos para que el máximo observado en la carga de benchmark deba ser ≤50 ms» | Definir máximo observado como criterio de pase y propagar la carga (100 calentamientos, 1 000 mediciones, 5 000+ acciones, K por defecto) por spec, plan, tasks, research y quickstart. |
| 2026-11-09 | Antigravity (Gemini 3.8 Flash) | «/speckit.specify Capacidad: terreno y cazador. Desde el punto de vista del juego, las salidas ahora tienen un costo de tránsito y aparece un enemigo que persigue al jugador por la ruta más barata [...] No mencionar estructuras de datos, clases ni módulos.» | Especificación formal de la capacidad 001 (terreno y cazador) en specs/001-terreno-cazador/spec.md con 4 historias de usuario priorizadas en formato Given/When/Then, requisitos funcionales FR-CAZ-01 a 15, entidades, criterios de éxito medibles, supuestos, feature.json y checklist de calidad requirements.md sin mención a estructuras de datos, clases ni módulos. |
| 2026-11-09 | Antigravity (Gemini 3.8 Flash) | «/speckit.clarify Resuelve y registra en el spec.md las siguientes preguntas de la especificación 001-terreno-cazador [...] 1. d == rango 2. puerta con cierre pendiente 3. costo d incluye salida a sala jugador 4. salas vecinas con salida cerrada 5. límite de actores por sala [...] Sin nombrar estructuras de datos, clases ni módulos.» | Integración de sección ## Clarifications (sesión 2026-11-09) y propagación a escenarios Given/When/Then, casos límite, requisitos funcionales FR-CAZ-03/05/06/07/10 y entidades en specs/001-terreno-cazador/spec.md; actualización de checklist de calidad a 16/16 conformes sin mención de estructuras de datos, clases ni módulos. |
| 2026-11-09 | Antigravity (Gemini 3.8 Flash) | «/speckit.plan Para la especificación 001-terreno-cazador. Restricciones obligatorias: Está PROHIBIDO usar heapq, deque y set (ni como estructura auxiliar). Implementa nuestra propia cola de prioridad / montículo. Evalúa en el plan si la lista enlazada de la agenda sirve para la ruta más barata o si es demasiado lenta; compara con montículo propio. Decide si cada cazador calcula por su cuenta o comparten cálculo. Cuándo reutilizar ruta e invalidación. Desempate menor id (FR-CAZ-09) y equivalencia cálculo desde cero (FR-CAZ-11). Bounded por rango (FR-CAZ-14). Cambios API: costo en salidas y cazador+rango en catálogo. Plan de medición --bench (FR-CAZ-15). Trazabilidad FR-CAZ-xx. Registra en DECISIONES.md.» | Generación del plan técnico completo para 001-terreno-cazador: specs/001-terreno-cazador/plan.md, research.md (evaluación montículo propio vs lista enlazada, estrategias individual acotada vs compartida, invalidación estricta de rutas y poda por rango), data-model.md (SalidaViva, Enemy, RutaCazador, DecisionCazador), contracts/interfaces.md (propuestas K1, K2, K3, K5 y CLI), quickstart.md (validación de los 7 escenarios del Apéndice B y métricas --bench), y registro formal de la Decisión 68 en DECISIONES.md con trazabilidad exhaustiva a FR-CAZ-01 hasta FR-CAZ-15. |
| 2026-11-09 | Antigravity (Gemini 3.8 Flash) | «/speckit.tasks Genera el tasks.md de 001-terreno-cazador a partir del plan. Cada tarea debe referenciar los IDs FR-CAZ-xx que cubre, y debe haber tareas de prueba para cada uno de los 7 escenarios de aceptación del Apéndice B, escritas antes de la implementación correspondiente. Incluye tareas para: costo de salidas e intervalo (FR-CAZ-01/02/03/12), comportamiento cazador (FR-CAZ-04 a 11), vista de costos y distinción de cazadores (FR-CAZ-13), rendimiento (FR-CAZ-14) y --bench (FR-CAZ-15). Verifica que ninguna tarea introduzca heapq, deque ni set.» | Generación estructurada de specs/001-terreno-cazador/tasks.md con 43 tareas divididas en 7 fases (Setup, Foundational, US1 a US4, Polish), con formato de checklist estricto, IDs T001 a T043, marcas [P] de paralelismo, trazabilidad [FR-CAZ-xx], enfoque TDD estricto con pruebas previas para cada uno de los 7 casos del Apéndice B, y verificación de exclusión total de heapq, deque y set. |
| 2026-11-16 | Antigravity (Gemini 3.8 Flash) | «/speckit.implement Implementa las tareas de 001-terreno-cazador en el orden de tasks.md. Reglas: no uses heapq, deque ni set; cada escenario de aceptación debe tener su prueba y pasar; no cambies decisiones del spec.md sin avisarme. Al terminar, ejecuta las pruebas y el --bench de esta capacidad y deja los resultados listos para DECISIONES.md.» | Ejecución íntegra y ordenada de las 43 tareas de specs/001-terreno-cazador/tasks.md: verificación y purga estricta de heapq, deque y set en código de la capacidad; modelos Exit.costo, SalidaViva.costo, Enemy.rango y puertas_version; dijkstra_acotado, distancias_desde_destino y dijkstra_individual con MonticuloMinimo y TablaIndice; desempate determinista por menor id e invalidación instantánea; suite completa de 19 pruebas en tests/test_terreno_cazador.py (100% de éxito en los 7 casos del Apéndice B y aclaraciones); suite bench_cazadores en src/orchestrator/bench.py evaluando los 5 ejes requeridos; registro de resultados empíricos en DECISIONES.md y 373 pruebas aprobadas en regresión total. |

## Continuación de 002 — 2026-11-09

- **Modelo:** Codex (familia GPT-6; variante no confirmada).
- **Prompt literal:** «qué hay pendiente para la persona B?» y «terminemos 002».
- **Uso:** revisión local de tareas, implementación y pruebas; correcciones de
  consola/viaje, reposición visual tras cruce, consultas de mochila, aislamiento
  de caché al cargar y detalles del mapa. Nuevas pruebas offline de conocimiento,
  deltas, viaje, interfaces, persistencia y replay; benchmarks de mapa/rutas con
  índice y heap propios frente a alternativas lineales. Resultados ejecutados y
  limitaciones se registran en quickstart y DECISIONES.md; no se atribuye cierre
  académico a pruebas sintéticas ni se implementa004 como parte de002.

- **Aclaración literal posterior:** «ya estan las instrucciones en docs».
  Uso: lectura íntegra de `docs/Cripta Parte II.md`, contraste de002, actualización
  de fuentes y eliminación del bloqueo por enunciado ausente; trazabilidad de los
  seis casos oficiales a IDs de requisito y pruebas automatizadas.

- **Consulta literal durante la ejecución:** «what else». Uso: estado de pendientes
  y rendimiento observado; ajuste documentado del muestreo de benchmarks después
  de una corrida exhaustiva demasiado costosa. No se atribuyen resultados a la
  matriz interrumpida; el diagnóstico inicial dirigido se distingue de la matriz
  final con costos recíprocos válidos.

- **Resultado ejecutado:** regresión final418 aprobadas/1 omitida (5,34 s);
  `--bench` salida0 y matriz final36 cargas en el informe JSON versionable de
  `docs/mediciones/`. Se publican fallos sintéticos de5 ms y el muestreo revisado;
  quedan46/52 tareas cerradas y seis de aceptación/integración pendientes.

## Preparación004 — 2026-11-10

- Prompt literal: «actualiza la preparación». Contexto: identificar trabajo de
  persona B que puede avanzar sin persona A.
- Uso: contraste de004 con `docs/Cripta Parte II.md` (§§3.6,5.5,6.1–6.3 y
  Apéndice B); actualización de spec, plan, research, tasks y quickstart.
- Resultado: T001 completada; T002/T003 conservadas pendientes por diferencias
  entre receptor propuesto004 y contrato aprobado002, y definición de v4.
  No se cambian código, contratos compartidos ni se atribuye aceptación ejecutada.
- Validación: revisión documental y `git diff --check`; sin pruebas funcionales
  porque solo se actualizaron documentos.

## Inicio de implementación004 — 2026-11-10

- Prompt literal: «sigamos con 004 para terminarlo».
- Uso: habilidad speckit-implement, prerrequisitos004 y checklist16/16; inspección
  del motor, agenda, RNG, undo, Sesión y persistencia. Propuesta concreta del
  receptor004 separado de002 y layout v4 en contracts/interfaces.md.
- Hallazgo: las inversas P1 omiten cambios que sí debe preservar la historia
  (pergaminos, RNG y operaciones de agenda posteriores al apilado). Se registra
  matriz preliminar de captura; no se marca T016 ni aceptación funcional.
- Pendiente: aceptación explícita T002/T003 conforme a la constituciónII y
  CONTRATOS.md regla6.3 antes de modificar interfaces compartidas.

## Requisito UI/UX de004 — 2026-11-10

- Prompt literal: «quiero resaltar la importancia de un buen UI/UX a la hora de implentar. no solo texto sin más. a la hora de implementar, revisar el resto de la implementación de interfaz y mantener consistencia además de buenas practicas como multiplos de 8px en bordes».
- Uso: inspección inicial de medidas, paleta y paneles existentes; incorporación
  de FR-LIN-15/16, tareas T031–T033 y criterios de validación visual. Retícula de
  8 px lógicos para espaciados/padding/radios y trazos finos permitidos.
- Resultado: alcance gráfico explícito con navegación, jerarquía, mapa histórico,
  foco, errores/vacíos y revisión visual/manual. No se implementa aún ni se
  consideran aprobados los contratos internos pendientes.
- Validación documental: git diff --check.

## Implementación004 y UI/UX — 2026-11-10

- Modelo: Codex; identificador específico del modelo no expuesto en esta sesión.
- Prompts literales: «sigamos con 004 para terminarlo»; «apruebo» (receptor
  histórico y formato v4); «recuerda hacer commit cada que sea necesario».
- Requisito UI/UX literal registrado arriba: consistencia con la interfaz
  existente, presentación visual y múltiplos de8 px.
- Uso: speckit-implement, revisión de contratos y auditoría de escrituras;
  diario de mutaciones, checkpoints, consultas puras t/#k, replay, v4 y validación
  candidata. Panel H/Historial con navegación, teclado/ratón, foco, sprites,
  barra de vida y grafo histórico. Tokens, paleta y fuentes compartidos.
- Validación: pruebas de estado completo, eventos empatados, antorcha/undo,
  pasos de viaje, corrupción/incompatibilidad y fallos inyectados; capturas
  revisadas con OfflineBackend real. Se distingue revisión headless de recorrido
  humano pendiente. Pruebas usan cuatro tamaños y contenido largo.
- Medición:5.000 esperar aceptadas mediante Sesión/motor, K10/20/50 y sin
  intermedios;100 calentamientos y1000 consultas por alternativa. K20: máximo
  2,862450 ms; RAM de estructura serializable39.122.486 bytes. Se conserva20
  por compromiso medido de memoria/latencia, sin extrapolar a otros estados.
- Commits locales por hitos: especificación/contratos antes del código; base002
  separada; motor004; correcciones, interfaz y evidencia en commits siguientes.
  No se hicieron operaciones remotas de GitHub. Archivos ajenos no se incluyen.
- Resultado funcional y detalles de regresión en quickstart.md; T033 queda
  abierto por recorrido humano. No se declara cierre académico total ni se
  adjudican001 o la revisión transversal completa§5.6 a esta entrega004.

- Regresión final004:464 aprobadas/1 omitida (14,39 s); git diff --check sin errores.

## Corrección visual004 — 2026-11-10

- Prompt literal: «remueve las esquinas redondeadas. eso aquí no se permite».
- Uso: eliminar redondeo en el historial y su botón de acceso, retirar el token
  de radio y corregir los criterios actuales de diseño. Los registros previos
  que describen radios reflejan la implementación anterior, reemplazada aquí.
- Validación: pruebas existentes de interfaz, regeneración y revisión de capturas
  offline a1024×800 y640×480, y git diff --check.
- Resultado de esta corrección:103 pruebas de interfaz aprobadas/1 omitida; capturas revisadas y ausencia de border_radius en src/view.

## Recuperación y validación de tipografía — 2026-11-10

- Prompts literales: «somwthing must have been left out before the force close.
  anything left behind? related with the fonts maybe»; «can you keep it going?
  do you need more context?».
- Modelo: Codex; identificador específico no expuesto en esta sesión.
- Uso: recuperar cambios locales de Lato y roles compartidos; revisar
  `docs/diseno-ui.md`; corregir distribución4K, mapa, nombres truncados, errores,
  contraste y resumen final. Añadir pruebas significativas de fuentes y tooltips.
- Validación:487 pruebas aprobadas/1 omitida; `git diff --check` sin errores.
  Capturas headless con FakeBackend/sprites reales a640×480,1024×800 y1280×720,
  con nombres/listas/errores largos, guardadas en `docs/mediciones/tipografia-*.png`.
  Detalle y límites en DECISIONES.md; no se declara recorrido humano ni
  conformidad WCAG completa. Sin operaciones remotas de GitHub.
- Los archivos ajenos `cache.pkl.fichas` y `docs/Cripta Parte II.md` se preservan.
- Prompts adicionales: «commit de eso»; «ocupo que te asegures que todo tengas
  mayusculas iniciales como minimo. muchos elementos se ven mal si están full
  en minúscula». Se añade mayúscula inicial a textos visibles y etiquetas de
  objetos, conservando siglas/datos originales. Se regeneran capturas y se
  valida con494 pruebas aprobadas/1 omitida (6,19 s), antes del commit local.

## Título y subtítulo sin fondo blanco — 2026-11-10

- Prompt literal: «el titulo y su subtitulo tiene un fondo blanco que no me
  gusta. además que el subtitulo no está ni centrado».
- Cambio: retirar ambos respaldos blancos del encabezado sobre arte; centrar
  cada línea del subtítulo y usar contorno oscuro de glifos para legibilidad.
- Validación:133 pruebas aprobadas/1 omitida; capturas actualizadas a640×480,
  1024×800 y1280×720 y selección revisada a resolución nativa. Sin recorrido
  humano interactivo. `git diff --check` sin errores.

## Proporción del título — 2026-11-10

- Prompt literal: «el tamaño del titulo no está proporcional. en ventanas
  pequeñas es muy grande y en ventanas grandes es muy pequeño».
- Cambio: tamaño final proporcional al arte de la caja, ajuste gradual por
  ancho y eliminación del doble escalado/fallback a fuente de botón.
- Validación:137 aprobadas/1 omitida; pruebas de proporción hasta4K, capturas
  actualizadas y revisión visual a640×480 y1920×1080. Se documenta la excepción
  del encabezado compacto en `docs/diseno-ui.md`.

## Cierre de 002: T052, T050, T049 y T051 — 2026-11-13

- Modelo: GLM-5.3-Flash Free vía OpenCode (asistente de código en terminal;
  sin atribución de proveedor adicional).
- Prompts literales: «empieza» (tras el informe de pendientes); «sí» (autoriza
  el commit por hito de T049); «no entiendo lo que dice la 47»; «pero no
  entiendo a que paquete se refiere. ya no hay entregables de parte del profe
  para este proyecto, te refieres a algo en su servidor?»; «pues creo que
  queda irresolvible».
- Prompts previos en la misma sesión (paráfrasis): preguntar qué queda en el
  proyecto; pedir ejecutar T050 y T052; pedir el siguiente paso.
- Uso: T052 verificada contra el 004 real con tres pruebas nuevas
  (reconstrucción por frontera de acción, concordancia deltas 002↔historia
  004, validación/conservación v4) y T050 con la regresión completa; T049
  ejecutada como recorrido offline con ejecutables reales y reloj/lector
  inyectados (consola en dos fases: demo real con oleadas/trampas y fixture
  limpia para las ramas ausentes del demo; vista headless SDL dummy a
  1024×800 y 640×480 con capturas en `docs/mediciones/002-t049-*`), con
  actualización de `README.md` (v4, U en recorrido, Escape fuera del panel);
  T051 como revisión de matriz FR/escenarios, declaración de pendientes
  (T046 bloqueada por la entrega de001 de la persona A, fuera del alcance de
  B; T047 como bloqueo externo sin resolución prevista según el equipo) y
  este registro.
- Aclaraciones registradas: se explicó que el «paquete oficial» de T047 es la
  cripta de referencia del enunciado §6.1 (no un servidor ni un entregable
  nuevo); con la evaluación del equipo de que no se publicará, T047 se
  declara bloqueo externo definitivo y la aceptación formal de002 queda
  incompleta, sin sustitutos sintéticos. El usuario aclaró además que 001 y
  003 pertenecen a la persona A y que él es la persona B, por lo que ambos
  bloqueos de002 quedan fuera de su alcance.
- Validación: regresión completa501 aprobadas/1 omitida (6,48 s), `git diff
  --check` sin errores; commits `db9be79` (T052/T050) y `e285829` (T049).
  Recorridos dirigidos, no partidas humanas; queda registrado en quickstart.
  El commit de T051 queda pendiente de autorización.

## T033 panel de historia — 2026-11-13

- Modelo: GLM-5.3-Flash Free vía OpenCode (misma sesión que la sección
  anterior).
- Prompt literal: «dale» (tras preguntar «¿Comiteo el hito T051 y sigo con
  T033?»); autoriza el commit y el recorrido del panel.
- Aclaraciones de la misma sesión: el usuario indica que 001 y 003 pertenecen
  a la persona A y él es la persona B, por lo que T046/T047 quedan fuera de
  su alcance; se corrige el registro de T051 en consecuencia.
- Uso: T033 como recorrido headless del panel de historia con ejecutables
  reales y fixture limpia (apertura, navegación por teclado y ratón, consulta
  inválida y válida, scroll con contenido extenso, cierre y verificación de
  ausencia de mutaciones); capturas a los tamaños admitidos en
  `docs/mediciones/004-t033-*`; ayuda completada en `README.md`; registro en
  quickstart y cierre de la casilla en `tasks.md` de004.
- Validación: verificación de controles íntegros en las cinco resoluciones;
  igualdad de `a_dict`, bitácora, pila, reloj, posición, sala y viaje antes y
  después del recorrido. Regresión completa y commit en la sección de T033
  del quickstart de004; recorrido dirigido, no partida humana interactiva.

## Especificación de verificación de resolubilidad — 2026-11-16

- Modelo: GPT-6 (Codex; identificador exacto de variante no expuesto).
- Prompt (paráfrasis): ejecutar `$speckit-specify` para comprobar antes de jugar
  si la cripta puede ganarse usando esqueleto y ubicaciones de llaves; devolver
  orden determinista o diagnóstico con llaves inaccesibles, frontera, ubicaciones
  y ciclo concreto; permitir `--forzar` y `--verificar <cripta>` sin vista;
  mostrar reporte al iniciar; exigir ≤ 200 ms, crecimiento aproximadamente lineal,
  recorrido compartido sin recorridos por llave y consumo de la consulta dentro
  de `presupuesto_solicitudes`; no mencionar estructuras de datos, clases ni módulos.
- Uso: creación de `specs/005-verificacion-resolubilidad/spec.md`, checklist de
  calidad y actualización de `.specify/feature.json` conforme a la habilidad.
  Se conservó el antecedente 003 sin modificarlo. Se documentaron los supuestos
  sobre llaves opcionales, rutas alternativas, ciclos, errores de información y
  condiciones de medición. No se modificaron código, interfaz ni contratos.
- Validación: revisión documental de consistencia con constitución, enunciado
  y contratos; checklist 16/16. Comprobación de artefactos y `git diff --check`;
  no corresponde ejecutar pruebas de código ni afirmar mediciones de rendimiento.

## Aclaraciones de 003-resolubilidad — 2026-11-16

- Modelo: GPT-6 (Codex; variante exacta no expuesta).
- Prompt (paráfrasis): aplicar `$speckit-clarify` a003 y registrar seis respuestas
  sobre desempate determinista, puertas sin llave o ubicación, multiplicidad de
  llaves y puertas, selección de ciclos, declaración de salida en P1 y formato
  textual del reporte; aplicar P1 donde responda y preguntar las ambigüedades,
  sin nombrar estructuras de datos, clases ni módulos en el spec.
- Uso: se registraron las respuestas de P1 sobre reutilización de llaves,
  llave única por puerta y datos generales de salida; se añadieron requisitos
  y escenarios pertinentes. Las decisiones no resueltas por P1 se consultan
  secuencialmente, sin convertir supuestos anteriores en decisiones aceptadas.
- Validación parcial: lectura de P1 §2.1, §2.4, §2.5 y §3; checklist16/16 →15/16
  mientras se aclaran las decisiones pendientes. Sin cambios de código ni
  mediciones de rendimiento. No hay `.specify/extensions.yml` ni hooks registrados.

- Respuesta posterior del usuario: «A». Se registra la distinción entre puerta
  cerrada sin llave declarada (error sin veredicto) y llave declarada ausente
  de consulta completa (bloqueada/no obtenible, ubicación no declarada), en
  Clarifications, FR-RES-14, escenarios7/8 y Assumptions de003.

- Cierre de aclaraciones: el usuario responde «todo lo recomendado. luego me
  dices que es». Se aplica A para orden de descubrimiento (salas por descubrimiento,
  salidas N/S/E/O, llaves según consulta) y se concretan las recomendaciones
  restantes: un ciclo bloqueante, primero según el orden declarado de entrada y
  seguimiento de dependencias; reporte textual común en español con secciones,
  identificadores, ubicaciones y categorías vacías explícitas. Se registran las
  seis respuestas solicitadas en Clarifications, FR-RES-05/07/10/14/15,
  escenarios y criterios de aceptación; sin nombres de estructuras, clases ni
  módulos en el spec. Se activa003 en `.specify/feature.json` por la selección
  explícita del usuario. Preguntas formuladas:2; respondidas:2 (la segunda junto
  con autorización para resolver las restantes recomendaciones).
- Validación final documental: checklist15/16 →16/16, sin regresiones ni
  pendientes de calidad. El único cambio del checklist fue el marcador del
  requisito de comprobabilidad. Verificada coherencia de los seis registros,
  ausencia de términos prohibidos y `git diff --check`; sin pruebas de código
  ni mediciones, pues el cambio es documental. El contraste del enunciado íntegro
  de P2 y las mediciones de rendimiento siguen pendientes para aceptación futura.

## Plan003-resolubilidad — 2026-11-16

- Modelo: GPT-6 (Codex; variante exacta no expuesta).
- Prompt (paráfrasis): ejecutar `$speckit-plan` para003, prohibir heapq/deque/set
  incluso auxiliares; un recorrido incremental compartido con reporte/orden,
  determinismo, `/llaves` presupuestado/persistible por versión, forzar/verificar
  sin vista, reporte gráfico,≤200 ms, benchmark único vs repetido por llave con
  sintéticas encadenadas por semilla; compartir esqueleto con001, trazar FR-RES
  y registrar estructuras justificadas por mediciones en DECISIONES.md.
- Aclaración: se preguntó por ciclos de alternativas frente a dependencias
  inevitables; el usuario preguntó qué se recomienda y autorizó «pues hazlo»
  tras recomendar ciclo concreto acompañado de todas las alternativas aún
  bloqueadas. Se actualizó FR-RES-07/15, aclaración y escenario13 sin nombres
  de estructuras, clases ni módulos en el spec. Desempate concretado por primera
  llave participante según consulta y primer retorno con orden fijo.
- Uso: plan.md, research.md, data-model.md, quickstart.md y propuestas de
  contratos de API/Sesión/CLI/UI y esqueleto compartido. Investigación delegada
  conforme a speckit-plan para revisar ciclos y medir alternativas estructurales.
  Script y JSON de medición en docs/mediciones/003-estructuras-plan.*;
  decisiones y limitaciones en DECISIONES.md. Sin implementación del verificador,
  tareas, commits, cambios a contratos firmados ni llamadas remotas.
- Validación: microbenchmarks estructurales ejecutados (dos calentamientos y
  siete muestras, semilla300316, checksums), revisión documental/IDs/enlaces,
  restricción terminológica del spec y git diff --check. No se afirma ejecutar
  pruebas del verificador, capturas de la UI ni200 ms en la cripta publicada.
  No hay archivo extensions.yml ni hooks registrados para plan.

- Revisión final del plan003: compuerta explícita para llaves antes de salidas;
  índice textual FNV-1a64 medido frente a codificación entera/búsqueda lineal,
  con comparación de igualdad completa. Se descarta codificación entera por su
  peor costo con enteros largos, sin atribuir ventaja temporal a FNV. Cifras
  actualizadas a la última ejecución. Plan, contratos, modelo y guía verificados;
  spec conserva IDs FR-RES-01–15 y ausencia de términos de implementación.

## Tareas003-resolubilidad — 2026-11-16

- Modelo: GPT-6 (Codex; variante exacta no expuesta).
- Prompt (paráfrasis): ejecutar `$speckit-tasks` para003 a partir del plan;
  cada tarea debe referenciar FR-RES, incluir pruebas previas de los cuatro
  escenarios del Apéndice B, consumo /llaves, recorrido único con orden/reporte,
  forzar/verificar sin vista, reporte gráfico y benchmark; ninguna introduce
  heapq, deque ni set.
- Uso: generado `specs/003-resolubilidad/tasks.md` con47 tareas:2 setup,
  6 fundamentos,31 US1 (única historia del spec),8 transversales y8 oportunidades
  paralelas. T009–T012 prueban B1–B4 antes de sus implementaciones; compuerta
  T009–T018 antes de T019. Contratos, shared001, presupuesto, alternativas de
  ciclo y aceptación de200 ms conservan las condiciones del plan.
- Validación documental: IDs T001–T047 consecutivos, referencias FR-RES-01–15,
  casillas/etiquetas/rutas/dependencias previas, matriz de cobertura, precedencia
  de pruebas y prohibiciones comprobadas. Sin código ni pruebas ejecutadas de
  la funcionalidad; sin modificaciones al spec/plan ni aprobación implícita
  de contratos. No hay extensions.yml ni hooks previos/posteriores.

## Implementación003-resolubilidad — 2026-11-16

- Modelo: GPT-6 (Codex; variante exacta no expuesta).
- Prompt (paráfrasis): ejecutar `$speckit-implement` por orden de `tasks.md`, sin
  heapq/deque/set y con un solo recorrido incremental; probar todos los
  escenarios, no cambiar decisiones del spec sin aviso, correr suite y `--bench`
  y dejar evidencia lista para DECISIONES.md.
- Autorización de diseño: el usuario aprobó las propuestas mientras mantengan
  coherencia con el resto del proyecto, incluidas las decisiones compartidas.
  `specs/003-resolubilidad/spec.md` no se editó durante la implementación.
- Uso: DTO/endpoint/cache offline, propagación con cola propia, diagnóstico
  residual iterativo, política de inicio/CLI/reporte visual y benchmark sintético;
  integración construida sobre el modelo compartido de salas. Se añadió
  `--verificar` y `--forzar`; las fixtures no usan HTTP real.
- Validación: prueba dirigida del adaptador legacy `tests/test_llaves.py` y
  `tests/test_sesion_resolubilidad.py`: 13 aprobadas. En la API, solo se adapta
  la forma exacta `{llaves: [...]}` del endpoint no paginado, usando la versión
  validada de la ficha; `spec.md` permanece intacto. En `cripta-06` (300 salas,
  versión `f9ed9afa683d`) se midieron 100 verificaciones completas: mediana
  1.504 ms, máximo 7.660 ms, todas bajo 200 ms. Evidencia:
  `docs/mediciones/003-resolubilidad-publicada.json`.
- Validación: `.venv/bin/python -m pytest tests/ -q`: 573 aprobadas/1 omitida;
  `.venv/bin/python -m src.main --bench` terminó con código0 e incluyó 003.
  Los benchmarks sintético y publicado están en sus JSON bajo
  `docs/mediciones/`; la auditoría AST y `git diff --check` pasan. El comando
  integral tarda unos seis minutos porque ejecuta también las cargas históricas.
  La secuencia test-first de T009–T018 no se puede afirmar como cumplida: se detectó
  que el núcleo ya estaba escrito antes de cerrar el registro de fallos previos;
  se conserva esa desviación explícita y las pruebas no se debilitaron.
- Integración remota: `origin` solo publica `main`, igual a `HEAD` local en
  `b81b1af`; no existe rama publicada separada de001. `gh auth status` muestra
  token local inválido, pero el fetch público de `origin/main` funcionó sin
  autenticación y no encontró commits nuevos.

## 2026-11-16 — Codex (GPT-6)

Prompt (paráfrasis): corregir pendientes de 001, conectar 001/003 con 002/004 siguiendo Spec Kit y realizar commits por hitos. Uso: revisión de convergencia, tareas correctivas y validación por pruebas offline; resultados se registran al ejecutar cada hito.

Continuación2026-11-16: se integró el proveedor neutral en turnos del cazador, se añadió ocupación de salas sin contenido y persistencia5 selectiva, con pruebas primero de cierre inicial y entrada enemiga. Se retiró SalidaPonderadaFalsa de fixtures002; la prueba de Sesión usa Exit/SalidaViva reales y verifica reloj ponderado ida y viaje automático de vuelta. Validación localizada:98 pasan; cierre completo todavía pendiente.

Continuación2026-11-16 (paráfrasis): corregir coherencia física de puertas y deshacer. Uso: función común de puerta recíproca, sincronización al incorporar salas y regresión de victoria al abrir desde salida; suite completa599 pasan/1 omitida.

Continuación2026-11-16: medición del drenaje real para no atribuir a decisiones aisladas la aceptación del ciclo; siete muestras54,5–92,4ms, resultado negativo registrado. Se agregó función reproducible y métricas del drenaje a bench_cazadores; no se declara rendimiento logrado.

Continuación2026-11-16: optimización del ciclo real y receptor004 mediante reutilización de ubicación, distancias inversas dirigidas para rangos grandes y sincronización por segmentos; nuevas pruebas de equivalencia, ausencia de alias y fallo atómico. No se declara cumplido el objetivo20ms; se mantiene T047 abierta.

Continuación2026-11-16: cierre integrado T046/T047 de002 con001 real y referencia publicada compartida de003. Se añadieron pruebas de sesión y medición reproducible offline;1000 rutas máximo3,802311ms sin fallos5ms. Se corrigieron contadores para excluir preparación y se registraron ambas ejecuciones.

Continuación2026-11-16: reducir costo residual del ciclo completo con historia. Uso: medición amplió alcance a acción+drenaje+cierre, optimización de recorridos/eventos y sincronización RNG con regresión; medición final22,49–28,18ms, no cumple20ms. Se conservaron evidencias negativas y pendienteT047.

Continuación2026-11-16: diario estructural de agenda y alta incremental de pila, con prueba primero del número de serializaciones. El benchmark ahora mide ciclos nuevos con historia y descarta caché accidental en mediciones de rango.48 pruebas específicas pasan; siete ciclos14,6–18,0ms. No se declara cierre de001.

Continuación2026-11-16: cerrar aceptación001/004 y escalabilidad con actor distante. Uso: TablaIndice de localización, pruebas integradas reales, corrección RNG al deshacer y compatibilidad4/5 por deltas mínimos;608 pruebas aprobadas/1 omitida, decisión local<1ms y ciclo13,82ms máximo. CLI --bench completo iniciado; no se declara terminado antes de su salida.
