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
