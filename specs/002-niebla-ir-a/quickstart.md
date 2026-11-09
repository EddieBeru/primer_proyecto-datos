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
