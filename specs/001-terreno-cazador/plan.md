# Implementation Plan: Terreno y cazador (001)

**Branch**: `001-terreno-cazador` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification aclarada en `specs/001-terreno-cazador/spec.md`, con las 5 aclaraciones formales de la sesión 2026-11-09 y restricciones obligatorias del usuario.

---

## Summary

La capacidad introduce costos de tránsito diferenciados en las salidas de las salas (afectando la duración del cruce para todos los actores según $\max(1, \text{costo} \times 100 // \text{velocidad})$) y un nuevo comportamiento de enemigo «cazador» dotado de un atributo `rango`. En su turno, el cazador prioriza el ataque cuerpo a cuerpo si comparte sala con el jugador; si no, calcula la ruta de costo mínimo $d$ hacia el jugador a través de salidas abiertas usando una búsqueda de Dijkstra acotada por su rango. Si no hay ruta o $d > \text{rango}$, espera consumiendo costo 100; si $d \le \text{rango}$, avanza un paso por la ruta óptima desempatando por la vecina de menor `id`.

El enfoque técnico utiliza un montículo binario mínimo propio (`MonticuloMinimo`) y tablas hash de direccionamiento abierto/encadenamiento propio (`TablaIndice`) desarrolladas en el proyecto, descartando terminantemente `heapq`, `deque`, `set` y `dict` como índices evaluados. Se incorpora invalidación estricta de rutas por versión de puertas (`puertas_version`) y posición del jugador para garantizar equivalencia observable absoluta con un cálculo desde cero (`FR-CAZ-11`).

---

## Technical Context

**Language/Version**: Python $\ge 3.11$ (entorno de ejecución verificado: Python 3.12).

**Primary Dependencies**: Estándar del proyecto (`pygame-ce` para interfaz gráfica, sin librerías externas de grafos o colas). `pytest` para la suite de pruebas.

**Storage**: Guardado binario propio (`savegame.py`, formato K2). Los costos de salidas y fichas de enemigos se incorporan en la estructura de datos. Las trayectorias calculadas son transitorias en memoria y no se serializan.

**Testing**: `pytest` con ejecuciones offline, proveedores sintéticos y desacoplados de la red HTTP.

**Target Platform**: Linux / Windows escritorio, soporte para consola interactiva, modo `--bench` y vista Pygame.

**Project Type**: Capacidad del motor de juego distribuida entre C1 (persistencia/modelos), C2 (reglas y algoritmos de combate/movimiento), orquestador (medición y ciclo) y vista.

**Performance Goals**:
- Ciclo de eventos completo entre dos decisiones del jugador $\le 20\text{ ms}$ con decenas de cazadores activos (`FR-CAZ-14`, `SC-CAZ-01`).
- La decisión de un cazador de rango pequeño ($R$) crece en función de la región alcanzable dentro de su rango ($V_R$), siendo independiente del tamaño total de la cripta ($|V|$) (`SC-CAZ-02`).

**Constraints**:
- **Prohibición absoluta**: PROHIBIDO usar `heapq`, `deque` y `set` (ni como estructura auxiliar). No usar `dict` como índice evaluado.
- Implementación de colas de prioridad y tablas mediante estructuras propias en `src/estructuras/`.
- Determinismo y equivalencia observable con cálculo desde cero en cada turno (`FR-CAZ-11`).
- Desempate estricto por menor `id` numérico de sala vecina (`FR-CAZ-09`).

**Scale/Scope**: Criptas de 10 a $10\,000$ salas; escenarios con hasta 50 cazadores concurrentes; rangos de costo desde 100 hasta $50\,000$.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principio Constitucional | Pre-Fase | Post-Diseño | Evidencia y Justificación |
| :--- | :--- | :--- | :--- |
| **I. Cumplimiento del Enunciado** | Cumple | Cumple | Cumple todas las reglas de combate (P1 §2.8), duración de acciones y reescalado de velocidad (P1 §2.3) e intervalos de reloj virtual. |
| **II. Separación de Responsabilidades** | Cumple | Cumple | C1 extiende `Exit` y `Enemy`; C2 implementa la lógica de búsqueda y decisión; vista consume `FotoEstado`; C1 y C2 no se importan mutuamente. |
| **III. Estructuras y Algoritmos Justificados** | Cumple | Cumple | Prohibición estricta de `heapq`/`deque`/`set`. Se justifica en `research.md` y `DECISIONES.md` la elección de `MonticuloMinimo` sobre listas enlazadas. |
| **IV. Reproducibilidad y Determinismo** | Cumple | Cumple | Desempate por menor `id`; equivalencia observable con recálculo desde cero; compatibilidad con `--replay` en reloj virtual. |
| **V. Validación Proporcional** | Cumple | Cumple | 7 escenarios del Apéndice B cubiertos con pruebas unitarias específicas y suite `--bench` en `quickstart.md`. |
| **VI. Desarrollo Guiado por Spec Kit** | Cumple | Cumple | Sigue el flujo: `spec.md` -> `clarify` -> `plan.md` -> `research.md` -> `data-model.md` -> `contracts/` -> `quickstart.md`. |
| **VII. Registro de LLM** | Cumple | Cumple | Todas las sesiones y prompts se documentan en `PROMPTS_LLM.md`. |

---

## Project Structure

### Documentation (this feature)

```text
specs/001-terreno-cazador/
├── spec.md                   # Especificación funcional validada y aclarada
├── checklists/requirements.md# Checklist de calidad 16/16
├── plan.md                   # Este plan de implementación
├── research.md               # Investigación técnica, comparación de estructuras y decisiones
├── data-model.md             # Modelos de datos, entidades y diagramas de estado
├── contracts/interfaces.md   # Propuesta de contratos K1, K2, K3, K5 y CLI
└── quickstart.md             # Guía ejecutable de validación y escenarios del Apéndice B
```

### Source Code Layout (cambios previstos)

```text
src/
├── estructuras/
│   ├── monticulo_minimo.py     # Heap binario mínimo propio (cola de prioridad)
│   └── tabla_indice.py         # Tabla hash propia con encadenamiento amortizado
├── modelos/
│   ├── rooms.py                # Exit.costo (entero >= 1, default 100)
│   ├── catalog.py              # Enemy: comportamiento "cazador", rango (int >= 1)
│   └── conocimiento.py         # DatosSalida.costo (coordinado con 002)
├── controller2/
│   ├── modelo.py               # SalidaViva.costo, EstadoPartida.puertas_version
│   ├── enemigos.py             # Lógica de decisión del cazador y desempate menor id
│   ├── movimiento.py           # Ejecución de paso, incremento de puertas_version
│   └── reloj.py                # intervalo(costo, velocidad) y reescalar()
├── orchestrator/
│   ├── sesion.py               # Drenaje de turnos y sincronización con FotoEstado
│   └── bench.py                # Micro-benchmarks de la suite de cazadores (FR-CAZ-15)
└── view/
    ├── ui.py / sf.py           # Presentación de costos en salidas y distinción del cazador
tests/
└── test_terreno_cazador.py     # Suite de pruebas unitarias y de los 7 casos del Apéndice B
```

---

## Architecture & Implementation Design

### 1. Evaluación de Estructuras: Montículo Propio vs. Lista Enlazada Ordenada

Se evaluó la cola de prioridad de lista enlazada de la agenda de eventos frente a `MonticuloMinimo`:
- **Lista Enlazada Ordenada**: Las inserciones requieren búsqueda lineal $O(V)$, lo que genera un costo global de $O(V^2)$ para Dijkstra. Con $V = 1\,000$ salas, requiere $\approx 1\,000\,000$ operaciones. **Descartada por lenta**.
- **Montículo Binario Mínimo Propio (`MonticuloMinimo`)**: Opera en un arreglo contiguo (`list` como array de base). Inserciones y extracciones en $O(\log V)$. Complejidad total $O((V + E) \log V) \approx 50\,000$ operaciones para $1\,000$ salas ($> 20\times$ más veloz). **Seleccionada**.
- Las etiquetas de distancia exploradas se almacenan en `TablaIndice` propia, sin usar `dict` como índice evaluado.

### 2. Estrategia de Persecución: Individual Acotado vs. Compartido

- **Cálculo Individual Acotado (Motor / Turnos ordinarios)**:
  - Dijkstra iniciado en la sala del cazador $u$.
  - **Poda por Rango (`FR-CAZ-14`)**: No se insertan en el montículo salas cuyo costo acumulado tentativo supere el `rango`. Si el montículo se agota sin llegar al jugador, se concluye $d > \text{rango}$ en tiempo proporcional a la bola $B(u, \text{rango})$ sin explorar el resto de la cripta.
- **Cálculo Compartido Inverso (Soporte `--bench` / Múltiples Cazadores)**:
  - Dijkstra iniciado en la sala del jugador, acotado por $\max_{h}(\text{rango}_h)$.
  - Dado que los costos de salida son simétricos (`FR-CAZ-01`), la distancia $dist(u, jugador) == dist(jugador, u)$.
  - Permite a $N$ cazadores consultar su distancia y la de sus vecinas en $O(1)$.
- **Determinismo y Equivalencia (`FR-CAZ-11`)**: Ambas estrategias producen exactamente la misma decisión observable.

### 3. Regla de Desempate Estricto por Menor ID (`FR-CAZ-09`)

Sea $u$ la sala actual del cazador. Para todas las vecinas $v$ accesibles por una salida abierta en ese instante:
1. Calcular el costo total de la ruta a través de $v$: $d_v = \text{costo}(u, v) + \text{dist}(v, \text{jugador})$.
2. Determinar la distancia mínima global: $d = \min_{v} d_v$.
3. Si no hay ruta transitable o $d > \text{rango}$, el cazador espera con costo 100.
4. Si $d \le \text{rango}$, obtener el conjunto de vecinas óptimas:
   $$V^* = \{ v \mid d_v == d \}$$
5. Avanzar hacia la vecina $v^* = \min(V^*)$ según su identificador numérico entero `v.id`.

### 4. Política de Invalidación de Rutas

Una ruta en memoria se reutiliza únicamente si se cumplen simultáneamente:
1. `ruta.sala_jugador == estado.sala_actual` (el jugador no se ha movido).
2. `ruta.puertas_version == estado.puertas_version` (ninguna puerta se ha abierto o cerrado).
3. El cazador está en la sala prevista y la ruta tiene pasos pendientes.
- La muerte de otros actores o cambios de velocidad **no** invalidan la ruta (`FR-CAZ-03`).
- Cualquier discrepancia fuerza un cálculo fresco desde cero (`FR-CAZ-11`).

### 5. Extensiones al API y Catálogo

- `Exit.costo`: entero $\ge 1$ (default 100).
- `SalidaViva.costo`: entero $\ge 1$ (default 100).
- `Enemy.comportamiento`: incluye `"cazador"`.
- `Enemy.rango`: entero $\ge 1$ (obligatorio para cazadores).
- Intervalo de movimiento: $\max(1, \text{costo\_salida} \times 100 // \text{velocidad})$.

---

## Matriz de Trazabilidad de Requisitos (FR-CAZ-01 a FR-CAZ-15)

| Requisito | Descripción | Componente en el Plan | Contrato / Diseño | Validación / Quickstart |
| :--- | :--- | :--- | :--- | :--- |
| **FR-CAZ-01** | Costo en salidas ($\ge 1$, default 100, simétrico) | `Exit`, `SalidaViva` | K1 (§1.1), `data-model.md` | `test_costo_salida_default_y_simetria` |
| **FR-CAZ-02** | Intervalo $\max(1, \text{costo} \times 100 // \text{vel})$ | `reloj.py`, `movimiento.py` | K1 / C2 | Apéndice B, Caso 6 |
| **FR-CAZ-03** | Universalidad a actores; errante/rastreador conservan reglas | `enemigos.py`, `reloj.py` | C2 | `test_errante_rastreador_costos` |
| **FR-CAZ-04** | Comportamiento cazador y campo rango | `Enemy`, `catalog.py` | K1 (§1.2), `data-model.md` | `test_catalogo_cazador_rango` |
| **FR-CAZ-05** | Orden de turno: atacar $\to$ calcular $d$ $\to$ esperar $\to$ mover | `decidir_accion_cazador` | C2 / `enemigos.py` | `test_cazador_orden_turno` |
| **FR-CAZ-06** | $d$ suma salidas abiertas en ese instante | Dijkstra acotado | `rutas.py`, `enemigos.py` | `test_cazador_salidas_abiertas_instante` |
| **FR-CAZ-07** | Espera con costo 100 si no hay ruta o $d > \text{rango}$ | `decidir_accion_cazador` | C2 | Apéndice B, Casos 1 y 2 |
| **FR-CAZ-08** | Mover un paso por ruta de costo $d$ si $d \le \text{rango}$ | `decidir_accion_cazador` | C2 | Apéndice B, Caso 3 |
| **FR-CAZ-09** | Desempate por menor `id` de vecina | Desempate explícito | C2 / `enemigos.py` | Apéndice B, Caso 4 |
| **FR-CAZ-10** | Conoce esqueleto y puertas; ignora niebla; no abre puertas | Dijkstra sobre topología | C2 | `test_cazador_no_abre_puertas_ignora_niebla` |
| **FR-CAZ-11** | Equivalencia observable con cálculo desde cero | Política de invalidación | C2 / `research.md` (§3) | Apéndice B, Caso 5 |
| **FR-CAZ-12** | Reescalado de velocidad proporcional (P1 §2.3) | `reloj.reescalar` | C2 / `reloj.py` | Apéndice B, Caso 7 |
| **FR-CAZ-13** | Visualización de costos y distinción visual de cazador | `FotoEstado`, Pygame/Consola| K5 (§4.1) | `test_vista_muestra_costos_y_cazador` |
| **FR-CAZ-14** | Rendimiento: ciclo $\le 20\text{ ms}$; costo acotado a región | Poda por rango en heap | C2 / `monticulo_minimo` | `SC-CAZ-01`, `SC-CAZ-02` |
| **FR-CAZ-15** | Medición comparativa en `--bench` | `orchestrator/bench.py` | CLI (§5) | `cazador-suite` en `--bench` |

---

## Complexity Tracking

| Decisión / Estructura | Por qué es necesaria | Alternativa más simple rechazada y motivo |
| :--- | :--- | :--- |
| **Montículo binario mínimo propio** | Garantiza $O((V+E)\log V)$ en Dijkstra para cumplir $\le 20\text{ ms}$. | Lista enlazada de la agenda: rechazada por costo cuadrático $O(V^2)$ que supera 100 ms en grafos grandes. |
| **Poda de búsqueda por rango** | Permite que cazadores con rango pequeño tarden $< 1\text{ ms}$ en mapas de $10\,000$ salas. | Dijkstra global en toda la cripta: rechazada porque violaría `FR-CAZ-14` al tardar proporcional a toda la cripta. |
| **Contador `puertas_version`** | Invalida de forma instantánea ($O(1)$) cualquier ruta en caché al cambiar una puerta. | Comparación exhaustiva del grafo o recálculo incondicional siempre: overhead innecesario en puertas estables. |
