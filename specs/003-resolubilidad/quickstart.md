# Guía de validación 003 — Resolubilidad

Estado: implementación local validada el 2026-11-16. La consulta de ubicaciones
de llave se integra con C1 y el modo offline usa paquetes versionados. Las
fixtures de esta capacidad son sintéticas y no representan una cripta publicada.

## Pruebas

Desde la raíz del repositorio:

```bash
python -m pytest tests/test_resolubilidad.py tests/test_llaves.py tests/test_almacen_llaves.py -q
SDL_VIDEODRIVER=dummy python -m pytest tests/test_vista_resolubilidad.py -q
python -m pytest tests/test_sesion_resolubilidad.py tests/test_cli_resolubilidad.py tests/test_bench_resolubilidad.py -q
python -m pytest tests/ -q
git diff --check
```

La suite cubre los trece escenarios de aceptación, incluidos B1–B4, validación
estricta y budget/reintentos HTTP simulados, caché fría/caliente, inicio forzado
y protegido, modo de verificación sin vista, igualdad del reporte y SDL dummy.
Las pruebas no realizan peticiones HTTP reales. Última suite completa:
**573 passed, 1 skipped** con `.venv/bin/python -m pytest tests/ -q`.
`git diff --check` termina sin errores.

Nota de secuencia: las pruebas T009–T018 existen y pasan, pero durante el trabajo
el núcleo T019–T027 se había implementado antes de cerrar el registro de sus
fallos previos. Por tanto, no se afirma que el gate test-first de esa fase se
haya cumplido históricamente. No se cambiaron expectativas para hacer pasar el
código.

## Fixtures y ejecución offline

`tests/fixtures/resolubilidad/` contiene esqueleto y respuestas de llaves de
igual versión para `resoluble`, `ciclo` e `incompleta`. Puede reproducirse la
CLI con:

```bash
python -m src.main --offline tests/fixtures/resolubilidad --verificar resoluble
python -m src.main --offline tests/fixtures/resolubilidad --verificar ciclo
python -m src.main --offline tests/fixtures/resolubilidad --verificar ciclo --forzar
python -m src.main --offline tests/fixtures/resolubilidad --jugar --cripta ciclo
python -m src.main --offline tests/fixtures/resolubilidad --jugar --cripta ciclo --forzar
python -m src.main --offline tests/fixtures/resolubilidad --verificar incompleta --forzar
```

Los códigos de verificación son 0 (resoluble), 1 (no resoluble) y 2
(incompleta/error). Verificar solo no instancia Pygame ni crea partida, catálogo
o bitácora. `--forzar` permite iniciar solo con un resultado negativo completo;
una consulta incompleta sigue bloqueando.

## Auditoría estructural y regresión compartida

```bash
python -m pytest tests/test_restricciones_resolubilidad.py -q
python -m pytest tests/test_esqueleto.py tests/test_datos_conocimiento.py tests/test_tabla_indice.py tests/test_viaje.py tests/test_historia.py tests/test_cli_historia.py tests/test_savegame.py tests/test_sesion.py -q
```

La auditoría inspecciona AST de algoritmo, DTO, cliente, almacén, sesión, vista,
reportes, benchmark, fixtures y pruebas nuevas. El flujo revisado no importa ni
usa `heapq`, `deque`, `set` o `frozenset`, no ordena mediante `sorted`/`sort` y
no retira elementos con `pop(0)`. La vista tocada también usa listas/tuplas para
estas marcas y cursores para sus colas. No se declara cumplimiento global para
legados ajenos al flujo.

### Revisión de la conexión con001

En `origin/main` ya existen piezas generales reutilizables: `DatosSalida.costo`,
Dijkstra (`src/algoritmos/rutas.py`), la función genérica
`intervalo(costo, velocidad)` del reloj y etiquetas de costo en el mapa. Sin
embargo, el `Exit` del proveedor/modelo aún no parseaba costo y la sesión agenda
movimientos con costos fijos; los turnos de enemigos también usan100. No hay
comportamiento/rango `cazador` en `src/`, ni decisión que lo conecte con Dijkstra,
ni benchmark de CAZ. Esta implementación añadió `Exit.costo` default100 y su
validación/serialización al modelo compartido para completar el enlace de datos
con003. Dijkstra existente es una pieza disponible, no evidencia de que FR-CAZ
esté implementado ni de que el cazador deba usarlo sin contrastar FR-CAZ-14.

## Benchmark de 003

```bash
python -m src.main --bench
```

El comando ejecuta las mediciones existentes del proyecto y la sección
`003_resolubilidad`; esta última queda guardada en
`docs/mediciones/003-resolubilidad-sinteticas.json`. La semilla es 300316; usa
dos calentamientos y siete muestras por tamaño/familia para cadenas, ciclos,
puertas pendientes, alternativas y desconexión, en tamaños 128/512/2048/8192.
Generación, comparador repetido y medición de memoria se mantienen separados de
la sección temporizada. Se registran compilación, propagación, resumen, texto,
visitas, mediana/máximo, bytes de IDs/reporte y colisiones de cubeta del índice
textual. La referencia lenta repite alcanzabilidad por llave y solo se mide
para cadenas de hasta 512 llaves.

Corrida final del benchmark de capacidad, semilla300316, Python3.12.3, Linux
x86_64, Intel Core i7-1185G7@3.00GHz, commit base `b81b1af`; dos calentamientos,
siete muestras por caso. Resultados de las cargas mayores:

| Familia | S | E | K | Mediana ms | Máximo ms | Bytes reporte |
|---|---:|---:|---:|---:|---:|---:|
| Cadena | 8194 | 8193 | 8193 | 165.27 | 191.03 | 291540 |
| Ciclo | 8194 | 8193 | 8193 | 245.63 | 264.22 | 1187078 |
| Pendientes | 8195 | 32772 | 8194 | 348.49 | 417.24 | 291568 |
| Alternativas | 8195 | 8194 | 8193 | 152.79 | 158.32 | 291540 |
| Desconexión | 8195 | 8193 | 8193 | 151.37 | 159.92 | 291540 |

El caso de ciclo reporta un texto de1187078 bytes; pendientes tiene cuatro
salidas por sala. En los cinco casos mayores hubo 2151 colisiones de cubeta de
IDs (máximo5 IDs por cubeta); bytes de IDs ≈138 KB. El JSON conserva las siete
muestras y fases de cada tamaño/familia, contadores, referencias lentas cuando
corresponde, memoria máxima y entorno. La medición sintética muestra costos de
diagnóstico/texto y no supera el umbral en todas las familias; la aceptación
publicada se mide por separado abajo.

## Vista

La pantalla muestra el reporte común antes de crear el estado de partida. Se
puede volver y, tras negativo, continuar solo si se eligió forzar. Las pruebas
SDL dummy comprueban igualdad textual, navegación, error no forzable, foco y
scroll de identificadores largos. `python docs/mediciones/003-reporte/capturar_estados.py`
regenera menú, selección, nombre completo por tooltip, reporte largo/error y
scroll, HUD, mapa e historial en640×480,1024×800 y1280×720. La revisión headless
confirmó que el texto largo de selección está completo al enfocar/pasar el
ratón, el panel de reporte envuelve/recorre IDs largos, botones no cubren el
panel, y el mapa/historial conservan navegación visible. El contraste medido
para reporte texto/panel es13.57:1, título/panel6.92:1 y texto claro/acción
6.81:1 (todos ≥4.5:1). Son comprobaciones de estas parejas; no una afirmación
de conformidad WCAG global. La captura/revisión no equivale a un recorrido
humano; este último sigue pendiente.

Inspeccioné visualmente las 27 capturas generadas, en las tres resoluciones y
estados. Detecté que en 640×480 el badge numérico invadía el indicador de salas
de las tarjetas; ajusté los márgenes UI sin reducir la tipografía. `test_tarjeta_compacta_separa_badge_del_nombre_y_datos`
comprueba la geometría y las capturas se regeneraron. También comprobé el
scroll del reporte largo, botones, mapa e historial. Esto sigue siendo revisión
de imágenes más pruebas SDL; no un recorrido manual de la aplicación.

## Aceptación en cripta publicada

La API pública lista `cripta-06` («Cripta de referencia», 300 salas); los datos
generales y sus seis páginas de esqueleto responden con versión
`f9ed9afa683d`. Su `GET /criptas/cripta-06/llaves` devuelve cuatro ubicaciones,
pero el JSON real solo contiene `{"llaves":[...]}`. El adaptador acepta esa
forma exacta, propia del endpoint no paginado, y fija ID/versión desde los datos
generales ya validados; otras formas siguen sujetas al DTO versionado estricto.
La elección conserva `spec.md` y queda cubierta por pruebas de forma legada,
versión ausente, payload mal formado y DTO incompleto.

La instantánea cruda quedó guardada en
`docs/mediciones/003-reporte/003-resolubilidad-publicada-paquete.json` (96,801
bytes; SHA-256 `f1de59fbd0e884428e7a04c5151f7c0ca78cd0c88d9326d8719c5329570adabb`).
`python docs/mediciones/003-reporte/obtener_paquete_publicado.py` la renueva y
conserva la respuesta literal sin rellenar los metadatos ausentes.

Con `cripta-06` ejecutamos cien verificaciones completas (preparación local,
propagación, resumen, ciclo y texto; sin red/render), tras dos calentamientos.
Las 100 quedaron bajo 200 ms: mediana 1.504 ms, máximo 7.660 ms, estado
resoluble; el paquete crudo de 300 salas ocupa 96,801 bytes. El artefacto
conserva cada muestra, versión, contadores y entorno en
`docs/mediciones/003-resolubilidad-publicada.json`.

## Matriz de requisitos y aceptación

| Requisito | Prueba/evidencia |
|---|---|
| FR-RES-01 | `tests/test_sesion_resolubilidad.py`, `tests/test_cli_resolubilidad.py` |
| FR-RES-02 | escenarios 2/5 y `test_salidas_automaticas_y_trampas_no_bloquean_y_llave_no_se_consumen` |
| FR-RES-03 | escenarios 1/6/8 y `test_escenario13_ciclo_de_alternativas_y_otras_causas` |
| FR-RES-04 | escenarios 3/9 y comparador del benchmark pequeño |
| FR-RES-05 | escenario 9, repetición determinista, auditoría estructural |
| FR-RES-06 | escenarios 1/8 y frontera exacta en `tests/test_resolubilidad.py` |
| FR-RES-07 | escenarios 1/10/13 y selección del primer ciclo según consulta |
| FR-RES-08 | escenario 4; pruebas de Sesión, CLI y vista |
| FR-RES-09 | `tests/test_cli_resolubilidad.py`, subprocess offline sin vista |
| FR-RES-10 | `tests/test_vista_resolubilidad.py`, continuar/volver y negativo no forzable |
| FR-RES-11 | `tests/test_llaves.py`, `tests/test_almacen_llaves.py`, CLI offline |
| FR-RES-12 | contadores y `docs/mediciones/003-resolubilidad-sinteticas.json`; 100 muestras publicadas en `docs/mediciones/003-resolubilidad-publicada.json` |
| FR-RES-13 | referencia repetida frente a incremental en `tests/test_bench_resolubilidad.py` |
| FR-RES-14 | escenarios 7/8, tipos estrictos, incompleta e inicio protegido |
| FR-RES-15 | texto compartido CLI/Sesión/vista, categorías vacías e IDs completos |

| Escenario | Prueba/evidencia |
|---|---|
| 1 | `test_escenario1_llave_final_detras_de_su_puerta_no_resoluble` |
| 2 | `test_escenario2_llave_de_errante_en_sala_inicial` |
| 3 | `test_escenario3_orden_determinista_por_descubrimiento_y_consulta` |
| 4 | `test_negativo_bloquea_sin_crear_estado_y_forzar_conserva_reporte`; CLI/view |
| 5 | `test_escenario5_reutiliza_llave_en_puertas_distintas` |
| 6 | `test_escenario6_usa_salida_y_llave_declaradas_en_info` |
| 7 | `test_escenario7_puerta_cerrada_sin_llave_es_error` |
| 8 | `test_escenario8_llave_requerida_ausente_es_no_obtenible` y alternativa abierta |
| 9 | `test_escenario9_n_antes_de_e_y_llaves_locales_segun_consulta` |
| 10 | `test_ciclos_independientes_solo_reporta_el_primero_segun_consulta` |
| 11 | `test_resultado_se_ve_antes_de_instalar_foto_y_contenido`; CLI report |
| 12 | `test_reporte_negativo_sin_ciclo_y_con_categorias_vacias` |
| 13 | `test_escenario13_ciclo_de_alternativas_y_otras_causas` |

Las capturas y el script están en `docs/mediciones/003-reporte/`. La revisión
headless de las pantallas solicitadas está hecha; T045 permanece abierta solo
para el recorrido humano.
