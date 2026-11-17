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
