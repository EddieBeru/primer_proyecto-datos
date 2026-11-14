# Guía de validación: 002

Esta guía reúne comandos, criterios y evidencias de implementación de002. Los pasos manuales y benchmarks se identifican por separado y no se consideran ejecutados hasta registrar su resultado. Ver [spec](spec.md), [modelo](data-model.md) y [contratos](contracts/interfaces.md).

## Preparación

Desde la raíz del repositorio, con Python≥3.11:

```bash
.venv/bin/python -m pip install -r requirements.txt pytest
```

Durante planificación `.venv` tenía Python3.12.3 y no tenía pytest. La instalación de pytest se completó después, como registra T003.

**Estado al iniciar implementación, 2026-11-08 (T003):** instalado pytest9.2.0 en
`.venv`, sin agregar dependencias de ejecución. Verificado con
`.venv/bin/python -m pytest --version`. La instalación inicial falló por DNS dentro
del sandbox; se completó mediante la solicitud de acceso a red de la terminal.
Las fuentes locales continúan siendo P1 (`docs/enunciado.md`) y la guía resumida
de parte II; no se encontró el enunciado íntegro oficial P2. El contraste y la
aceptación académica siguen pendientes, sin presentar la guía como documento
oficial. No se detectó una nueva contradicción esencial en esta revisión; cualquier
contradicción posterior bloquea solo la decisión afectada. T003 registra este estado,
pero no satisface su condición adicional de contraste para el cierre completo.

La aprobación explícita del usuario («apruebo todos los contratos») y la enmienda por contrato constan en T001 y `CONTRATOS.md`. La aceptación académica de costos/tiempos ponderados reales aún depende de la entrega de001; los falsos solo dan evidencia aislada.

## Pruebas automatizadas previstas

Crear suites `test_conocimiento.py`, `test_rutas_conocidas.py`, `test_viaje.py` durante implementación, con proveedores sintéticos. Extender suites existentes para contratos cruzados.

```bash
.venv/bin/python -m pytest tests/test_conocimiento.py tests/test_rutas_conocidas.py tests/test_viaje.py -q
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python -m pytest tests/test_vista.py tests/test_sesion.py tests/test_savegame.py tests/test_gamelog.py tests/test_doc_oficial.py -q
.venv/bin/python -m pytest tests/ -q
```

No activar `CRIPTA_API_REAL`: la suite de vista tiene una prueba remota optativa. Una prueba que necesite servicio se distingue de las offline.

| Grupo | Escenarios y comprobaciones |
|---|---|
| Conocimiento | Sala inicial explorada; avistada solo ID; desconocida ausente. Precargar varias salas no revela. Consulta/foto sin mutaciones. |
| Antorcha | Revelación inmediata al encender y al entrar; abierta/cerrada indistintas; sin contenido/activación remota; vecinos de vecinas solo avistados. No actualizar puerta remota conocida ni inventar observación desconocida. |
| Puertas | Observar desde ambos extremos recíprocos; cierre local actualiza memoria en evento, remoto conserva recuerdo. Al acercarse durante ruta, recalcular con nueva observación sin cobrar intento fallido. |
| Undo | Revertir entrada con antorcha y encendido; recuperar estados previos/ausencia, efecto anterior, inventario, reloj y agenda. Cinco pasos son cinco intervalos; consulta/cancelación no ocupan pila. Mantener exclusión de pergaminos y caché. |
| Rutas | Más salas pero menor costo; empate por primer vecino menor aunque se descubra después; ciclos/costo1, arcos paralelos y IDs dispersos. Excluir avistadas/desconocidas/puertas desconocidas. Falso que falle si búsqueda consulta grafo vivo o contenido. |
| Viaje | Destino actual/no explorado; enemigos vivos iniciales; dormidos al entrar que después mueren; muertos no bloquean; daño de cualquier origen aunque se cure después; puerta bloqueada y ausencia de ruta; ninguna apertura automática. |
| Control | Cancelar entre pasos, sin movimiento adicional/tiempo; U cancela y deshace último paso. Teclas sostenidas también cancelan antes del siguiente cruce automático. Consultar mapa/foto/inventario/ayuda conserva el viaje. Guardar/pausar, instalar una carga válida y error del viaje/fin detienen la continuación. Una carga fallida conserva el viaje incluso tras mostrar su error, sin aplicar limpieza general. Movimiento manual sigue cruzando por proximidad sin confirmación. |
| Log/carga | Comentario una vez, movimientos individuales; ambos replay ignoran comentario. Comparar conocimiento lógico, RNG, reloj y sala original/reproducida. Roundtrip v3, datos corruptos y rechazo explícito v1/v2; carga fallida normal/en frío no reemplaza partida ni cancela su viaje. |
| Integración004 aislada (T043) | Colector falso recibe deltas antes/después ordenados y truncamiento, incluso después de más de cinco acciones; el motor no guarda historia completa ni usa snapshots por acción. |
| Integración004 real (T052) | Tras disponer de004 compatible, comparar conocimiento histórico antes/después de entrada, antorcha y retroceso; verificar reconstrucción correcta y conservación de la historia al guardar/cargar. Registrar resultado o bloqueo: el falso no cierra FR-NIE-08. |

Cubrir todos los escenarios1–11 de spec. Las pruebas del plan no sustituyen aceptación completa de004 (historia/checkpoints) ni001 (cazadores/costos globales).

## Recorrido manual offline

El paquete actual `paquete_demo` permite comprobar controles/carga básicos; no garantiza por sí solo todas las ramas de002 ni costos ponderados. Para esos casos usar fixtures sintéticas de las nuevas suites, sin afirmar que el demo trae los datos nuevos.

```bash
.venv/bin/python -m src.main --jugar --offline paquete_demo --cripta cripta-ejemplo
.venv/bin/python -m src.main --vista --offline paquete_demo
```

Tras implementación, consola: ejecutar `mapa`, explorar normalmente, volver a pedir mapa, ordenar `ir a <id_explorado>` y cancelar con `cancelar` antes del siguiente cruce. Esperar control manual en la última sala alcanzada, motivo visible y mismo reloj que al terminar ese paso. Destino no explorado debe rechazarse sin tiempo. Encender antorcha con `usar <id>` cuando se posea una; comprobar revelación inmediata y después deshacer con un pergamino disponible.

Con viaje activo, consultar `mapa`, `foto`, `inventario` y `ayuda`: el viaje se conserva. Intentar cargar un archivo inválido y mostrar el error: la sesión y el viaje anteriores se conservan y permiten continuar desde el mismo punto; probar este flujo con lector/reloj inyectados, sin avance intercalado durante la comprobación. Una carga válida instala la partida con viaje inactivo.

Pygame: M abre el mapa gráfico de nodos cuadrados y puertas; ↑/↓/←/→ seleccionan en cada dirección y Enter inicia viaje; Escape lo cancela. Comprobar que mapa no expone nombres de avistadas y que WASD vuelve a control manual sin paso automático adicional. Cruzar una puerta manualmente acercándose sigue funcionando. Probar U durante recorrido y guardar/cargar tras varios pasos.

## Mediciones reproducibles previstas

```bash
.venv/bin/python -m src.main --bench
```

Extender `correr_todo` con `bench_conocimiento` y `bench_ir_a`; conservar bench existentes. Semilla20261106;100/1 000/10 000 salas, grado≤4, cadenas/mallas/empates, mapas parciales/completos y puertas estables/desactualizadas. Generación fuera del tramo medido.

- 100 calentamientos y 1 000 consultas por carga; reportar mediana, p95 y máximo en ms, CPU/SO/Python, semilla, V/E conocidos, muestras y máximo de memoria. Calcular estadísticas con ordenamiento propio, sin trasladar una estructura evaluada a biblioteca.
- Medir consulta puntual, construcción de mapa completo y siguiente paso por separado. Búsqueda no incluye HTTP, renderizado ni drenaje. El límite≤5 ms se verifica sobre cálculo de cada paso medido en referencia offline completa, informando también máximo/fallos, no solo promedio.
- Registrar referencia con ID/versiones/semilla/V/E y máquina al obtener paquete oficial compatible; mientras no esté, publicar solo resultados sintéticos y dejar aceptación oficial pendiente.
- Contar registros de salas/puertas consultados o modificados al revelar exactamente las mismas vecinas sobre mapas conocidos crecientes; demostrar que las operaciones ordinarias no barren todo el mapa. Medir también secuencias que crucen los umbrales de expansión, incluyendo tiempo y registros recorridos en rehash dentro del costo total esperado amortizado. Distinguir operaciones ordinarias y expansiones sin excluir estas de SC-NIE-02; este acuerdo sigue pendiente del contraste oficial P2.
- Separar extracción de registros O(Vconocido+Econocido) y proyección ordenada mediante mergesort O(Vconocido log Vconocido+Econocido); no confundir la consulta del mapa completo con la revelación incremental. La vista reutiliza la proyección mientras el panel esté abierto y no cambie su revisión.
- Comparar índice propio con búsqueda lineal y heap propio con cola lineal. Registrar tamaño/tiempo/memoria y equivalencia de resultado, sin usar alternativa prohibida para resolver producción.
- Documentar resultados reales en DECISIONES.md y enlazar FR-NIE-19/20. La repetición completa de§5.6 y elección de K pertenecen al trabajo posterior de B, no a este plan de002.

## Cierre de implementación posterior

Plan→tasks→analyze antes de código. La entrega aislada de002 puede verificarse con proveedores y colectores falsos, declarando dependencias todavía no integradas. Aceptar completamente002 cuando los FR estén trazados y las pruebas pertinentes pasen, el mapa/undo/guardado/replay sean coherentes, las mediciones tengan evidencia y se cumplan las condiciones de T051. FR-NIE-08 requiere la prueba integrada real con004 de T052; mientras esté pendiente, no declarar aceptación completa ni presentar sus criterios como satisfechos por un falso.

## Evidencia de fundamentos — 2026-11-08

T002–T007 completadas. El índice propio maneja enteros/extremos, colisiones,
reemplazo, borrado y expansión al superar0,75; el heap mantiene orden estable sin
comparar valores. Los DTO validan costos, IDs y direcciones sin normalizarlos y
son inmutables. Las fixtures separan metadatos/contenido/fichas/activación, incluyen
IDs dispersos, arcos paralelos/recíprocos/no recíprocos y fallan ante accesos ocultos
dentro de `solo_metadatos`. Las salidas ponderadas son únicamente de prueba;
no se agregó costo a los modelos vigentes de001.

Comandos ejecutados y resultados:

```bash
.venv/bin/python -m pytest tests/test_tabla_indice.py tests/test_monticulo_minimo.py tests/test_datos_conocimiento.py -q
# 35 passed in 0.07s
.venv/bin/python -m pytest tests/test_tabla_indice.py tests/test_monticulo_minimo.py tests/test_datos_conocimiento.py tests/test_fixtures_niebla.py -q
# 42 passed in 0.09s
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python -m pytest tests/ -q
# 298 passed, 1 skipped in 3.21s
```

La prueba omitida es la integración real optativa de vista, sin `CRIPTA_API_REAL`.
No se ejecutaron benchmarks ni se afirma cumplimiento de5 ms. Esta evidencia
valida fundamentos, no los escenarios1–11 ni el cierre de US1. T001 continúa
pendiente de la aceptación del compañero; no se modificaron contratos vigentes
ni los formatos de partida/log/foto.

## Segundo avance y corte solicitado — 2026-11-08

Aprobación directa del usuario: «apruebo todos los contratos»; enmienda002
registrada en CONTRATOS.md. Las menciones anteriores de T001 pendiente describen
el estado previo a esa autorización. Se implementaron conocimiento/deltas,
rutas, control de viaje por pasos, mapa DTO, undo de antorcha, receptor de cambios,
comentario de replay y persistencia v3 con carga candidata. Consola y Pygame
todavía no conectan esos controles; no se declara completo002.

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python -m pytest tests/ -q
# 320 passed, 1 skipped in 2.92s
# Después de aislar el estado candidato de carga:
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python -m pytest tests/test_sesion.py tests/test_savegame.py tests/test_viaje.py tests/test_deltas_conocimiento.py -q
# 38 passed in 0.18s
```

La validación no sustituye los casos aún pendientes ni integra001/004. No se
ejecutaron benchmarks, recorrido manual ni aceptación oficial de rendimiento.

## Continuación — 2026-11-08

Se conectaron los controles de consola (`mapa`, `ir a <id>`, `cancelar`) y Pygame
(M abre el mapa, flechas seleccionan, Enter inicia y Escape cancela). El viaje
avanza un paso por intervalo de150 ms; consultas no lo cancelan y movimiento
manual sostenido lo cancela antes de reanudar el control. Se actualizó la ayuda
en `README.md`. Esta integración no se recorrió manualmente en el paquete demo;
queda pendiente T049. No se ejecutaron benchmarks ni integración con001/004.

Regresión ejecutada tras la integración de interfaz:

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python -m pytest tests/ -q
# 320 passed, 1 skipped in 2.93s (inicial integración consola/vista)
```

Después de esa corrida se hicieron retoques al mapa cacheado, teclado sostenido y
presentación; no se volvió a ejecutar la suite. La aceptación completa sigue
abierta: faltan validaciones ampliadas de carga y replay, mediciones sintéticas y
oficiales, recorrido manual y dependencias externas de001/004 y de la referencia P2.

Revisión visual del usuario (2026-11-08): aprobó la apariencia del mapa. Este
visto bueno no registra el recorrido manual de todos
los escenarios ni sustituye la regresión pendiente tras los últimos retoques.

## Verificación ampliada — 2026-11-09

Checklist de calidad: 16/16 puntos completos (solo lectura). Se seleccionó002
con `SPECIFY_FEATURE_DIRECTORY` absoluto y `SPECIFY_FEATURE_NO_PERSIST=1`, porque
el estado local de Spec Kit conserva004; no se cambió la capacidad activa global.
No hay `.specify/extensions.yml`: no hay hooks previos ni posteriores registrados.

Regresión final tras las correcciones y ampliaciones de pruebas:

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python -m pytest tests/ -q
# 415 passed, 1 skipped in 5.33s
```

La omitida sigue siendo la integración HTTP optativa. `git diff --check` y la
compilación de los módulos modificados también pasan. El resultado inicial de
esta sesión fue354 aprobadas/1 omitida: se añadieron61 casos efectivos.

Evidencia adicional:

- `tests/test_consola_viaje.py`: sondeo y reloj inyectados; mapa/foto/inventario/
  ayuda conservan continuación; mostrar error de carga permite el siguiente
  paso; guardar y cargar correctamente detienen; EOF/KeyboardInterrupt→130
  cancelan sin tiempo. No se usa terminal ni espera real en estas pruebas.
- `tests/test_vista.py`: separación mínima150 ms, cancelación sostenida antes de
  avance, panel sin movimiento, U revierte, reposición junto a puerta y
  `en_puerta`, mochila sin cancelación, caché por revisión, fallo de carga conserva
  controlador y temporizador. El mapa muestra costos/estados desde el DTO.
- `tests/test_sesion.py`: cargas normales/en frío con duplicados, destinos,
  referencias de puerta y deltas inválidos conservan estado/viaje; roundtrip v3
  permite deshacer; replay conserva conocimiento, sala, reloj y RNG. Candidato
  LRU aislado: una escritura de caché anterior al fallo no toca la activa.
- `tests/test_deltas_conocimiento.py`: colector recibe inicio/acción/evento,
  reaplicación y reversión recuperan el mapa esperado; más de cinco intervalos
  recibidos antes del descarte y truncamiento comprobados. Esto prueba el puerto
  de002, no implementa ni acepta004.
- `tests/test_bench_niebla.py`: heap/cola lineal equivalentes en cadenas, mallas,
  empates, conocimiento parcial y recuerdos desactualizados; conteo de rehash
  incluye cada registro movido. Las alternativas son implementaciones propias.

Recorridos adicionales, diferenciados de una sesión manual humana:

1. Ejecutable real `python -m src.main --jugar --offline ... --cripta
   cripta-ejemplo` en directorio temporal, con comandos por stdin: `mapa`, destino
   no explorado, `foto`, guardar, cargar, salir. Salida0; archivo creado,
   costos/salidas visibles y destino inválido rechazado. Transcripción temporal:
   `/tmp/cripta-002-consola.txt`.
2. Pygame con `OfflineBackend` y SDL dummy: iniciar, abrir mapa con M, dibujar
   captura1024×800 y revisar visualmente. Sala inicial identificada, dos vecinas
   solo avistadas sin nombre, conexiones y detalles de costos/puertas legibles.
   Captura temporal: `/tmp/cripta-002-mapa.png`. No equivale a jugar manualmente
   todos los escenarios; T049 conserva esa parte pendiente.

Pendientes externos: entrega ponderada001/coherencia física,
referencia oficial offline e historia004 para T052. No se solicitaron servicios
remotos ni se modificó código de cazadores/historia.


## Fuente oficial disponible y contrastada — 2026-11-09

El usuario indicó que las instrucciones ya están en docs. Se leyó completo
`docs/Cripta Parte II.md`; el contraste de002 con §§3.3–3.4,5.3,6.1–6.3,7.3 y
Apéndice B no encontró contradicciones esenciales nuevas. Se retira el bloqueo
por fuente ausente: T003 satisface ahora su condición de contraste. Las notas
anteriores sobre fuente faltante conservan únicamente valor histórico. La
referencia oficial para rendimiento y las entregas001/004 siguen pendientes.

| Caso Apéndice B | Requisitos | Prueba automatizada |
|---|---|---|
| Destino no explorado | FR-NIE-10 | test_controles_sin_tiempo_destino_actual_y_no_explorada |
| Puerta recordada abierta pero cerrada | FR-NIE-05/13/14/15 | test_puerta_cerrada_no_abre_aun_con_llave |
| Enemigos dormidos | FR-NIE-12/14 | test_dormidos_muertos_durante_drenaje_sin_dano_detienen_por_enemigos |
| Entrada con antorcha | FR-NIE-06/07 | test_entrada_con_antorcha_revela_sin_activar_y_deshace |
| Pergamino tras entrada con antorcha | FR-NIE-08 | test_entrada_con_antorcha_revela_sin_activar_y_deshace |
| Pergamino durante viaje | FR-NIE-17 | test_pergamino_revierte_solo_ultimo_paso_y_cancela |

La parte histórica de FR-NIE-08 sigue esperando004 real, aunque las pruebas
locales de conocimiento/guardado/undo pasen.


## Cierre de mediciones y regresión local — 2026-11-09

`--bench` terminó con salida0: matriz final36 cargas, semilla20261106,
1000/100/10 consultas por alternativa y100/10/1 calentamientos según tamaño.
Ver [informe JSON](../../docs/mediciones/002-niebla-2026-11-09.json) y la sección
«Mediciones finales de002» de [DECISIONES.md](../../DECISIONES.md). Se midieron
índice/lineal, mapa completo, heap/cola lineal, memoria auxiliar, revelación y
expansiones. Las36 comprobaciones de equivalencia pasaron. El método cambió por
el costo excesivo del muestreo inicial; motivación y límites en research/plan.

El máximo del heap en las cargas de100/1000/10000 salas fue23,142/86,251/452,053 ms.
No se acredita5 ms en estas cargas ni se certifica la referencia oficial ausente.
T045 se cierra como medición ejecutada con incumplimientos publicados y repetición
tras optimizar adyacencia; no como aprobación de FR-NIE-19. T048 consolida datos y
límites. Las tareas de aceptación integrada permanecen abiertas.

Regresión después del contraste oficial y la generación simétrica final:

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python -m pytest tests/ -q
# 418 passed, 1 skipped in 5.34s
```

Estado final de esta ejecución:46/52 tareas cerradas; pendientes T046/T047
(integración001 y referencia), T049 (recorrido manual completo), T050 (cierre de
regresión integrada, aunque la regresión local pasó), T051 (aceptación integral)
y T052 (conocimiento histórico con004 real). El enunciado P2 ya está contrastado.


## T052 y T050 — 2026-11-13

La entrega de004 (línea de tiempo, DECISIONES §D, 2026-11-10) ya es compatible:
formato v4, diario de escrituras, checkpoints y receptor de deltas en
`src/controller2/linea_tiempo.py`, conectado por la Sesión como
`receptor_historia`. Con eso se ejecutó T052 contra el 004 real, no el colector
falso de T043, en los tres archivos que la tarea indica:

- `tests/test_sesion.py::test_historia_conocimiento_entrada_antorcha_undo_carga`:
  sesión real con antorcha y entrada; `LineaTiempo.reconstruir` devuelve en cada
  frontera de acción el conocimiento exacto de ese momento (inicio de002,
  antorcha, entrada); el retroceso restaura la rama histórica hasta la antorcha
  y P1 concuerda; guardar/cargar v4 conserva `historia_accion(1..2)` y la
  reconstrucción final.
- `tests/test_deltas_conocimiento.py::test_receptor_historia_004_concuerda_con_deltas_002`:
  colector de002 y línea de004 montados a la vez; re-aplicar los deltas
  recibidos reproduce `estado.conocimiento` y las reconstrucciones históricas
  coinciden frontera a frontera; la lejana pasa de ausente a avistada (antorcha)
  y a explorada (entrada), y el deshacer la devuelve a avistada en ambas
  representaciones.
- `tests/test_savegame.py::test_historia_v4_conserva_y_valida_conocimiento`:
  roundtrip v4 conserva la historia completa; un guardado con conocimiento que
  no coincide con metadatos se rechaza con «conocimiento inválido» y un
  checkpoint histórico alterado con «historia inválida»; en ambos casos la
  sesión y su rama histórica quedan intactas.

Evidencia adicional previa que se mantiene vigente:
`tests/test_historia.py::test_historia_antorcha_entrada_undo_y_guardado` y
`tests/test_sesion.py::test_roundtrip_conocimiento_deltas_y_undo`. Con esto la
parte histórica de FR-NIE-08 queda verificada contra004 real. La dependencia
formal T046 (costo/tiempo ponderado de001, simetría y observación) sigue
abierta y bloquea la aceptación completa de002; este cierre no la alcanza.

T050: regresión integrada completa, con SDL dummy y sin `CRIPTA_API_REAL`:

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python -m pytest tests/ -q
# 501 passed, 1 skipped in 8.64s (antes: 498; +3 pruebas de T052)
git diff --check  # sin errores
```

La omitida es la integración HTTP optativa de vista. No se resolvieron
regresiones: no hubo fallos. Se conserva la separación de capas (004 no consulta
el motor al reconstruir; 002 sigue sin retener la historia completa ni elegir K)
y no se modificaron contratos, formatos de partida/log/foto ni reglas del motor.

Pendientes tras este cierre: T046/T047 (001 y referencia oficial), T049
(recorrido manual) y T051 (revisión de matriz y prompts; PROMPTS_LLM.md).

## T049 — 2026-11-13

Recorrido manual offline ejecutado con ejecutables reales y reloj/lector
inyectados (pasos de viaje deterministas, sin terminal real), diferenciado de
una partida humana. Transcripciones completas y capturas en `docs/mediciones/`
(`002-t049-*.txt`, `002-t049-vista-*.png`). Consola en dos fases, semilla
20261113, guardados v4 en directorio temporal:

- **Fase A — `paquete_demo` tal cual** (enemigos, oleadas cada 3000 y trampas
  vivos; combate reactivo del conductor, como una persona): `mapa` inicial con
  salidas/costos/puertas; `ir a 3` rechazado sin tiempo (destino no explorado);
  oleada programada a t=3000 y combatida; recogida y equipado de espada y
  escudo del propio demo; viaje 2→1 detenido por daño de trampas al entrar
  (`viaje detenido: dano`, §2.10/FR-NIE-12) y viaje 1→2 limpio completo. Al
  re-entrar en la sala 1, `llamas-01` aplica quemadura 80×3=240 que el antídoto
  no cura y la partida termina en `fin: derrota`. Limitación real registrada:
  el demo no permite recorrer las ramas de viaje limpio ni la rama
  antorcha+deshacer en una partida real (el pergamino está en la sala 5 y
  volver a la sala 1 con llamas armadas es mortal).
- **Fase B — fixture limpia** (sin enemigos, oleadas ni trampas, para las ramas
  que el demo no contiene): todas las ramas del recorrido previsto: mapa;
  rechazo de destino no explorado; cruce manual y recogidas; viajes 2→1 y
  2→1→3 completados; antorcha con revelación inmediata y `deshacer` con
  pergamino (el mapa anterior y posterior al retroceso concuerdan: la sala 2
  vuelve a avistada); con el viaje 5→3 pendiente, `foto` lo conserva, la carga
  de un archivo inexistente muestra un error amable y conserva sesión y viaje
  (confirmado con `foto`), `cancelar` detiene antes del segundo cruce con
  motivo visible y el reloj del último paso, y la carga válida instala la
  partida con viaje inactivo; `ir a 999` sigue rechazándose sin tiempo;
  `salir` → 0.
- **Vista Pygame (headless SDL dummy) a 1024×800 y 640×480**: cruce manual por
  proximidad sin paso automático adicional (reposo junto a la puerta); M abre
  el mapa: salas exploradas con nombre y avistadas sin nombre (el DTO no
  incluye `nombre` en avistadas); ↑/↓/←/→ seleccionan en cada dirección;
  Enter inicia el viaje solo hacia exploradas (sobre una avistada no hace
  nada); U durante el recorrido cancela el viaje y rebobina la última acción
  cerrada con 1 pergamino (un viaje sin pasos aún no tiene inversa: revierte
  el cruce anterior); Escape cancela el viaje con el panel abierto y también
  fuera del panel; en pausa G guarda y la carga válida restaura; la carga
  inexistente lanza `GuardadoError` con la sesión y el viaje intactos.
  Capturas: juego/mapa/viaje a 1024×800 y mapa a 640×480, legibles en ambos
  tamaños.

`README.md` actualizado: guardado v4 (el flujo rechaza v1/v2/v3), U durante el
recorrido, Escape fuera del panel y que el mapa no exponga nombres de
avistadas. Queda registrada la diferencia entre estos recorridos dirigidos y
una partida humana completa; T046/T047 siguen bloqueando la aceptación
completa de002.
