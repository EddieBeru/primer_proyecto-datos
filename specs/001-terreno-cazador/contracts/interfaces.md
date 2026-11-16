# Propuesta de Interfaces y Contratos: Terreno y Cazador (001)

Este documento describe las modificaciones e incorporaciones a los contratos de arquitectura `K1`, `K2`, `K3` y `K5` establecidas en `CONTRATOS.md`, preservando la estricta separación de capas entre C1, C2, el orquestador y la vista (Principio II de la Constitución).

---

## 1. Contrato K1: Proveedor de Datos (C1 → C2)

C1 entrega modelos de datos tipados; C2 nunca accede a sockets de red, archivos HTTP directos ni almacenamiento en disco crudo.

### 1.1 Salidas de Salas (`Exit`)
Se amplía la definición de `Exit` en `src/models/rooms.py` para incluir el atributo `costo`:

```python
@dataclass
class Exit:
    sala: int
    costo: int = 100                        # NUEVO (FR-CAZ-01): entero >= 1, default 100
    cerrada: Optional[bool] = None
    llave: Optional[str] = None
    cierre_automatico: Optional[int] = None # > 0
```

- En deserialización (`from_dict`):
  ```python
  costo_val = data.get("costo", 100)
  if costo_val is None:
      costo_val = 100
  costo = int(costo_val)
  if costo < 1:
      raise ValueError(f"costo de salida debe ser entero >= 1, recibido: {costo}")
  ```
- **Simetría**: Si `sala_A` declara salida a `sala_B` con costo $c$, C1 o el cargador garantizan que la salida recíproca de `sala_B` hacia `sala_A` posea el mismo costo $c$ (`FR-CAZ-01`).

### 1.2 Catálogo de Entidades (`Enemy`)
Se amplía la definición de `Enemy` en `src/models/catalog.py`:

```python
@dataclass
class Enemy:
    id: str
    nombre: str
    vida_max: int
    ataque: int
    defensa: int
    velocidad: int
    comportamiento: Literal["guardián", "errante", "rastreador", "cazador"] # Ampliado con "cazador"
    rango: Optional[int] = None                                           # NUEVO (FR-CAZ-04): unidades de costo
    suelta: Optional[list[str]] = None
    regeneracion: Optional[int] = None
```

- En `from_dict`:
  ```python
  rango_raw = data.get("rango")
  rango = int(rango_raw) if rango_raw is not None else None
  if data.get("comportamiento") == "cazador":
      if rango is None or rango < 1:
          raise ValueError("Enemigo cazador requiere campo 'rango' entero >= 1")
  ```

---

## 2. Contrato K2: Guardado y Carga (Persistencia)

- El formato de guardado binario conserva el estado de las salas, puertas y enemigos.
- **Transitoriedad de la caché de rutas**: La estructura interna `RutaCazador` **no** se serializa en el archivo de guardado `partida.bin`. Al cargar una partida, la caché de rutas de los cazadores inicia vacía y se recalcula bajo demanda en el primer turno de cada cazador, garantizando determinismo exacto y evitando incompatibilidades de formato binario.
- Se mantiene el soporte de validación de versiones de partida, rechazando archivos corruptos o incompatibles con `GuardadoError` según la regla constitucional IV.

---

## 3. Contrato K3: Bitácora y Replay

- Cada turno del cazador genera las líneas de bitácora correspondientes a su acción en `partida.log`:
  - Si ataca: línea estándar de combate idéntica a otros enemigos (`P1 §2.8`).
  - Si se mueve: línea de cambio de sala con el tiempo de llegada derivado de `max(1, costo_salida * 100 // velocidad)`.
  - Si espera: registro de turno en espera con costo 100.
- La reproducción de partidas mediante `--replay` reproduce de forma idéntica los turnos de los cazadores y sus tiempos en el reloj virtual, preservando el determinismo absoluto (`FR-CAZ-11`).

---

## 4. Contrato K5: Fachada hacia la Vista (C2 → Vista / Orquestador)

### 4.1 Proyección en `FotoEstado`
La vista consume exclusivamente la foto inmutable del estado proporcionada por `Fachada.foto()`:

- **Costos de Salidas**: Cada salida visible en la sala actual del jugador expone su `costo` (entero $\ge 1$). La vista gráfica (Pygame) y la consola muestran el costo de cada puerta abierta o accesible para que el jugador pueda tomar decisiones informadas (`FR-CAZ-13`).
- **Distinción Visual del Cazador**: En la lista de enemigos de la sala actual dentro de `FotoEstado`, los enemigos con comportamiento `"cazador"` se diferencian explícitamente (mediante etiqueta en consola y sprite/tinte diferenciado en Pygame) para distinguirlos de guardianes, errantes y rastreadores (`FR-CAZ-13`).

### 4.2 Métodos del Motor (C2)
Se incorpora en `src/controller2/enemigos.py` el soporte de decisión y turno para el cazador:

```python
def decidir_accion_cazador(
    estado: EstadoPartida,
    instancia_id: str,
    rango: int,
    catalogo: dict | None = None,
) -> tuple[str, int, int | None]:
    """Retorna (accion, costo_base, sala_destino).
    
    - accion: "atacar" (costo 100, destino None),
              "esperar" (costo 100, destino None),
              "mover"   (costo = costo_salida, destino = sala_vecina_id).
    Cumple FR-CAZ-05, FR-CAZ-06, FR-CAZ-07, FR-CAZ-08, FR-CAZ-09, FR-CAZ-11.
    """
```

---

## 5. Contrato CLI: Suite de Evaluación `--bench` (FR-CAZ-15)

El comando de línea de órdenes `python -m src.main --bench` se amplía con micro-benchmarks específicos para evaluar de forma reproducible:

```text
python -m src.main --bench --cazador-suite
```

Parámetros evaluados:
1. `cazador_1_vs_50`: Tiempo por ciclo de eventos con 1 cazador vs. 50 cazadores en cripta de 1 000 salas.
2. `cazador_rango_pequeno_vs_grande`: Tiempos de cálculo con $R=200$ vs. $R=5\,000$ en criptas de 100, 1 000 y 10 000 salas.
3. `cazador_compartido_vs_individual`: Comparativa entre Dijkstra acotado individual vs. Dijkstra compartido desde el jugador.
4. `cazador_reutilizacion_vs_recalculo`: Rendimiento de reutilización con invalidación estricta vs. recálculo total continuo, bajo escenarios con puertas estables y puertas con cierres automáticos periódicos.
5. `cazador_monticulo_vs_lista`: Comparativa de rendimiento entre `MonticuloMinimo` y lista enlazada ordenada en la búsqueda de caminos.
