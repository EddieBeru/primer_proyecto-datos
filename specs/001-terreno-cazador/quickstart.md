# Phase 1: Quickstart & Validation Guide — Terreno y cazador (001)

Esta guía documenta los escenarios ejecutables y comandos de validación para verificar de extremo a extremo la capacidad `001-terreno-cazador`, incluyendo los 7 casos de aceptación del Apéndice B y las mediciones de rendimiento de `--bench`.

---

## 1. Requisitos Previos y Entorno

- **Intérprete**: Python $\ge 3.11$ (entorno virtual activo).
- **Dependencias**: Instaladas desde `requirements.txt`.
- **Modo de ejecución**: Offline y desacoplado de la red (Principio V de la Constitución).

---

## 2. Comandos de Validación de Pruebas Unitarias y de Integración

Ejecutar la suite completa de pruebas específicas para la capacidad 001:

```bash
# Ejecución silenciosa y rápida
pytest tests/test_terreno_cazador.py -q

# Ejecución detallada con reporte de cada escenario
pytest tests/test_terreno_cazador.py -v
```

---

## 3. Verificación de los 7 Casos del Apéndice B

Las pruebas unitarias y de aceptación en `tests/test_terreno_cazador.py` validan de forma aislada e inequívoca cada uno de los 7 casos:

| # | Caso de Apéndice B | Prueba de Validación Asociada | Resultado Observable Esperado |
|---|---|---|---|
| **1** | Cazador sin ruta abierta hacia el jugador | `test_cazador_sin_ruta_abierta_espera()` | El cazador no cambia de sala, realiza la acción de espera y consume un costo fijo de 100 (`FR-CAZ-07`). |
| **2** | Ruta más barata supera el rango ($d > rango$) | `test_cazador_distancia_mayor_que_rango_espera()` | Permanece en su sala, espera y consume costo fijo de 100 (`FR-CAZ-07`). |
| **3** | Menos salas/mayor costo vs. más salas/menor costo | `test_cazador_prefiere_menor_costo_que_menos_salas()` | Elige la ruta de menor costo total acumulado $d$ en lugar de la ruta con menos saltos topológicos (`FR-CAZ-08`). |
| **4** | Dos vecinas inician rutas de costo mínimo idéntico | `test_cazador_desempate_menor_id()` | Se desplaza hacia la vecina $v$ con menor identificador entero (`min(v.id)`), cumpliendo `FR-CAZ-09`. |
| **5** | Puerta de la ruta se cierra entre dos turnos | `test_cazador_reaccion_puerta_cerrada_entre_turnos()` | En el turno siguiente decide como si calculara desde cero: toma un desvío abierto o espera si no hay camino viable (`FR-CAZ-10`, `FR-CAZ-11`). |
| **6** | Actor rápido atraviesa salida de costo 1 | `test_actor_rapido_costo_minimo_intervalo_al_menos_uno()` | Para velocidad 300 y costo 1, `max(1, 1 * 100 // 300) == 1`. El intervalo es al menos 1 tick virtual (`FR-CAZ-02`). |
| **7** | Cambio de velocidad en salida costosa | `test_actor_reescalado_velocidad_en_salida_costosa()` | Al alterarse la velocidad durante el cruce, el tiempo restante se reescala proporcionalmente según P1 §2.3 (`FR-CAZ-12`). |

---

## 4. Validación de Límites y Casos Borde (Clarifications)

Pruebas adicionales para las aclaraciones ratificadas:

```bash
# Validar caso frontera d == rango (el cazador avanza un paso)
pytest tests/test_terreno_cazador.py -k "test_cazador_frontera_d_igual_rango_se_mueve"

# Validar que puertas con cierre automático pendiente son transitables
pytest tests/test_terreno_cazador.py -k "test_puerta_con_cierre_pendiente_es_transitable"

# Validar inclusión del costo de la salida final hacia la sala del jugador
pytest tests/test_terreno_cazador.py -k "test_costo_total_incluye_salida_final_al_jugador"

# Validar combate inmediato cuando comparte sala con el jugador
pytest tests/test_terreno_cazador.py -k "test_cazador_comparte_sala_ataca_directo"
```

---

## 5. Medición de Rendimiento con `--bench` (FR-CAZ-14 y FR-CAZ-15)

Ejecutar la suite de micro-benchmarks comparativos en la consola:

```bash
python -m src.main --bench
```

### Métricas esperadas
1. **Tiempo de ciclo con 50 cazadores activos (`SC-CAZ-01`)**:
   - `cazadores_50_ciclo`: $\le 20\text{ ms}$ por ciclo de eventos entre dos decisiones del jugador.
2. **Escalabilidad por rango (`SC-CAZ-02`)**:
   - `cazador_rango_pequeno_10k`: $< 1.0\text{ ms}$ por decisión en cripta de $10\,000$ salas.
   - La variación del tiempo entre una cripta de 100 salas y una de $10\,000$ salas para un rango pequeño ($R=200$) debe ser menor al 10%.
3. **Comparativa de estructuras**:
   - `cazador_monticulo_minimo`: $< 0.5\text{ ms}$ vs. `cazador_lista_enlazada`: $> 10\text{ ms}$ en mapas medianos, justificando experimentalmente la elección en `DECISIONES.md`.

## Convergencia2026-11-16 (en curso)

`python -m pytest tests/test_terreno_cazador.py tests/test_historia.py tests/test_savegame.py tests/test_sesion.py tests/test_viaje.py -q`:98 pasan. Incluye planificación a través de salas descargadas, cierre inicial, entrada del cazador sin contenido/visita, persistencia5 y posterior hidratación conservando visitante/costos. No certifica aún ciclo completo de20ms ni cierre total de001.

Suite completa posterior: `python -m pytest tests/ -q`:598 pasan,1 omitida (13,27s). `git diff --check` sin errores.

2026-11-16: puertas recíprocas opuestas comparten apertura/cierre/deshacer mediante cambiar_puerta; incorporar una nueva sala conserva el extremo vivo. La regresión falló antes de corregir. Abrir desde la sala final registra también la puerta de salida. `python -m pytest tests/ -q`:599 pasan,1 omitida (15,36s). T046 de001 completada; rendimiento e integración final siguen pendientes.

Medición real del drenaje001: `python -c 'from src.orchestrator.bench import medir_ciclo_cazadores; print(medir_ciclo_cazadores())'`. Preparación de1000 salas/50 cazadores fuera del cronómetro; Sesion._drenar procesa eventos desde t1 hasta decisión del jugador en t100, sin red/render ni receptor histórico. Siete muestras en `docs/mediciones/001-ciclo-real-2026-11-16.json`:54,5–92,4ms, incumple20ms aun antes de añadir historia. El benchmark expone ahora claves drenaje_real para no confundir decisiones aisladas con aceptación. Perfil indica búsquedas repetidas y escaneos de actores; T047 permanece pendiente.

Optimización2026-11-16: se resuelve ubicación una vez por turno (regresión:6 recorridos antes,≤2 ahora), se corta el escaneo al encontrar actor y se elimina sincronización duplicada. CampoCazadores usa índice inverso propio sobre el esqueleto compartido; claves de validez:posición jugador,versión puertas,cantidad salas y rango cubierto. Arcos dirigidos y cierres comparados contra Dijkstra individual. Rangos≤200 conservan búsqueda individual local. Historia registra segmentos de agenda/pila y copia únicamente datos JSON del delta; no snapshots completos para deshacer. Se conserva publicación atómica ante fallo de registro. Suite posterior a optimización:601 pasan/1 omitida; aún falta aceptación20ms con receptor de historia (24–40ms observados) y prueba final de nuevas regresiones.

2026-11-16, seguimiento T047: el ciclo real incluye ahora esperar, drenaje y cierre histórico (antes medía solo drenaje sin acción). El receptor004 está activo por defecto. Se evitan recorridos de agenda para identificar el evento nuevo usando el intervalo de secuencias monotónicas; se omite revelación sin cambios para turnos/movimientos enemigos y se sincroniza RNG por identidad/contador propio (no por contador mutable de EstadoPartida). La regresión confirma actualización aun si el contador del estado ya coincide. Las conversiones de registros devuelven primitivos directamente. Suite completa:603 pasan/1 omitida; regresiones posteriores:80 pasan. Medición final:22,49–28,18ms, máximo28,175497ms, incumple20ms. Muestras completas en docs/mediciones/001-ciclo-historia-2026-11-16.json. T047 sigue abierta.

2026-11-16, diario estructural: Agenda conserva un diario optativo entre sincronizaciones (altas/bajas), sin activarlo en consumidores autónomos. Fachada aplica cada cambio mediante búsqueda binaria propia y publica segmentos históricos atómicamente, eliminando serializaciones completas por evento. La alta ordinaria de pila serializa solo la nueva inversa; descarte/retroceso y modificaciones de conocimiento usan diff general. La regresión que contaba serializaciones falló primero (5 llamadas) y ahora pasa con0. La prueba de20ms ya usa acción+drenaje+cierre histórico sobre1000 salas/50 cazadores, sin red/render ni preparación inicial dentro del reloj. Siete muestras posteriores:14,6–18,0ms.48 pruebas de001/historia/restricciones pasan. T047 permanece abierta hasta cerrar escalabilidad con ubicación distante y evidencia final; T048 requiere aceptación integrada adicional.

Validación final de este hito: `python -m pytest tests/ -q`:605 pasan,1 omitida (13,10s). Nueva medición sin procesos de prueba paralelos:11,06–15,69ms, máximo15,693099ms;7 muestras en `docs/mediciones/001-ciclo-diario-2026-11-16.json`. `git diff --check` sin errores.

## 2026-11-16 — Aceptación integrada001/002/003/004

`tests/test_integracion_001_004.py` usa modelos reales y ProveedorSesion: salida250, cazador activo, checkpoints, reconstrucción anterior a cada acción, carga en frío, replay completo e igualdad de salas/agenda/reloj/RNG/pila. Deshacer tras carga restaura RNG y permite continuar. La prueba detectó que el RNG no se revertía: ahora la inversa conserva solo estado/contador del generador (no snapshot de partida) y se reinstala el generador. Guardados4/5 anteriores sin esos campos recuperan solo RNG mediante deltas de la historia existente; prueba explícita de esquema anterior pasa. Proyecciones no generan falsos cambios por normalización tupla/lista.

Se añadió localización por TablaIndice en la fachada, preparada una vez y mantenida al cargar/entrar/oleadas/deshacer/revertir errores. La prueba con10000 salas falla si el turno intenta barrerlas. `python docs/mediciones/001-local/medir.py`:1000 decisiones frescas por mapa, mediana0,01643ms en100 salas y0,01706ms en10000 (variación3,8%), máximos0,170121/0,185839ms. Preparación excluida, localización indexada incluida y jugador distante. `docs/mediciones/001-local/resultado.json` guarda muestras.

`python -m pytest tests/ -q`:608 pasan,1 omitida (12,56s). Siete ciclos completos con inversas RNG:9,67–13,82ms, máximo13,81635ms; evidencia en `docs/mediciones/001-ciclo-integrado-2026-11-16.json`. T048 cerrada. T047 espera terminar el comando CLI --bench completo, actualmente en ejecución.
