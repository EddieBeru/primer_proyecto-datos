# Implementation Plan: Línea de tiempo

**Branch**: `main` (sin rama dedicada) | **Date**: 2026-11-08 | **Spec**: [spec.md](spec.md)

**Input**: `specs/004-linea-de-tiempo/spec.md`

## Summary

Entregar consultas históricas por reloj o acción durante una partida y desde
replay, sin mutar el estado activo. Se conservarán deltas inversos de C2 en
orden cronológico y checkpoints completos cada K acciones. Las consultas se
reconstruirán sobre estado aislado desde el checkpoint posterior más cercano,
aplicando como máximo K intervalos. El retroceso P1 seguirá limitado a cinco
intervalos; al usar pergamino, la línea 004 trunca la rama revertida y conserva
su ordinal separado para la nueva acción de pergamino.

## Technical Context

**Language/Version**: Python 3.11+; entorno local Python 3.12.

**Primary Dependencies**: biblioteca estándar, Pygame ya existente para la
aplicación; pytest para validación. No se requieren dependencias de ejecución
nuevas.

**Storage**: guardado binario P2. El formato actual v3 guarda conocimiento;
004 requiere un formato versionado que persista registros y checkpoints. Se
propone v4 en el contrato; P1 v1/v2 y P2 v3 sin historia se rechazan explícitamente.

**Testing**: pytest, priorizando fixtures/proveedores falsos y modo offline.

**Target Platform**: aplicación local de escritorio, Linux/macOS/Windows según
la compatibilidad ya mantenida por Python y Pygame; consola y replay sin vista.

**Project Type**: aplicación Python con capas C1/C2, orquestador y vista.

**Performance Goals**: máximo observado ≤50 ms en 1 000 consultas medidas tras
100 calentamientos, con al menos 5 000 acciones y K por defecto; reconstrucción
de como máximo K acciones; medir tiempo y memoria con al menos tres K y
alternativa sin checkpoints.

**Constraints**: no almacenar estado completo por acción; checkpoints separados
por K acciones; preservar determinismo de reloj, RNG, agenda y replay; no cambiar
la semántica P1 de pergamino ni el límite de cinco intervalos; no importar C1 en
C2 ni consultar red durante una reconstrucción histórica; usar búsqueda binaria
propia sobre cortes cronológicos y respetar las restricciones de estructuras
del enunciado.

**Scale/Scope**: mínimo verificable de 5 000 acciones por partida. El costo de
una acción puede incluir varios eventos automáticos; los benchmarks registrarán
acciones y deltas por intervalo. No se promete un límite de tamaño de estado no
definido en la guía.

## Constitution Check

| Principio | Gate antes de diseñar | Plan de cumplimiento |
| --- | --- | --- |
| I. Cumplimiento del enunciado | **Pasa como preparación documental**: P2 disponible y contrastado. | Véase research.md: §§3.6,5.5,6.1–6.3 y Apéndice B. Preservar P1 §2.11 y distinguir aclaraciones locales de reglas oficiales; aceptación ejecutada pendiente. |
| II. Separación y contratos | **Pasa con aprobación previa a implementación.** | `Sesion` coordina. C2 registra deltas e invierte sobre estado aislado; C1 solo persiste el DTO. Los contratos004 fueron aprobados explícitamente y registrados en CONTRATOS.md el2026-11-10. |
| III. Estructuras justificadas | **Pasa con evidencia pendiente.** | Guardar deltas y checkpoints; usar lista cronológica con búsqueda binaria propia; sin `sorted()` ni dict como índice evaluado; medir tres K y alternativa sin checkpoints. |
| IV. Determinismo/compatibilidad | **Pasa con cambio versionado.** | Registrar orden causal, reloj, RNG y agenda. Serializar línea completa en nuevo formato; rechazar explícitamente formatos sin línea y validar candidato antes de instalarlo. |
| V. Validación | **Pasa como plan; evidencia pendiente.** | Casos aislados offline para estado, replay, undo, carga y 5 000 acciones. Registrar omisiones y mediciones; no activar API real. |
| VI. Spec Kit | **Pasa.** | Aclaraciones aplicadas; plan, modelo, contrato y quickstart se generan antes de tareas/análisis/código. |
| VII. Trazabilidad LLM | **Pasa.** | Prompt resumido y uso de esta sesión registrados en `PROMPTS_LLM.md`. |

**Gate**: continuar con el diseño local. No empezar cambios funcionales hasta
que la propuesta de interfaz C2–orquestador quede aceptada por quienes comparten
el contrato. El enunciado P2 ya está disponible y contrastado; la aceptación final
requiere implementación, pruebas y mediciones, no solo esta preparación.

## Phase 0: Research summary

Ver [research.md](research.md). La elección es reconstruir desde checkpoint
posterior usando deltas inversos cronológicos: copia completa por acción viola
la restricción de memoria y replay desde inicio viola el límite K. `PilaDeshacer`
y `aplicar_inversa()` ofrecen una base en C2, pero el almacenamiento 004 será
independiente del tope P1 de cinco acciones. La rama vigente después de truncar
por pergamino conserva tiempos no decrecientes, incluidos tiempos repetidos; una
búsqueda binaria propia localiza el corte temporal.

## Phase 1: Design

- [Data model](data-model.md): registros inversos, checkpoints, línea vigente,
  cortes de consulta y resumen histórico.
- [Proposed contracts](contracts/interfaces.md): comandos, APIs de Sesión,
  captura desde C2, replay y compatibilidad de guardados.
- [Quickstart](quickstart.md): validación offline, determinismo, versiones y
  medición.

### Integration path

1. Auditar todas las mutaciones/eventos C2 y asegurar que su delta inverso queda
   completo y cronológico, incluyendo Agenda, RNG, mapa conocido y estados vivos.
2. Proponer/aceptar el receptor histórico C2 y su ciclo `registrar` → fin de
   acción/checkpoint → `truncar_intervalo`; mantener separado el colector de
   conocimiento definido por 002.
3. Implementar la línea y consulta aislada; verificar reloj `t`, acción `#k`,
   eventos empatados y no-mutación.
4. Integrar apertura/cierre de acción con `Sesion`, comando `historia`, replay
   hasta `t` y salida común de resumen. Cada paso automático es una acción.
5. Extender el binario a versión con historia; validar registros/checkpoints en
   candidato aislado. Rechazar P1 v1/v2 y P2 pre-004 v3 sin tocar partida/viaje.
6. Integrar retroceso: quitar eventos/checkpoints del intervalo revertido,
   conservar la rama previa, renumerar y registrar el uso aceptado del pergamino
   en el ordinal de 004 sin alterar contadores ni exclusiones P1.
7. Medir tres K, alternativa sin puntos de control, tamaño del estado y cantidad
   de deltas por intervalo; escoger el K por defecto con esos resultados.

### Risks and gates

- `PilaDeshacer` guarda solo cinco intervalos. No reutilizar su almacenamiento
  limitado ni dejar que el truncamiento de P1 borre historia 004 por accidente.
- Las rutas de evento que no pasan por `_apilar` pueden dejar la historia
  incompleta; deben hallarse antes de cerrar el receptor.
- El checkpoint posterior puede ser grande; el máximo de las 1 000 consultas
  debe medirse incluyendo la copia aislada y la aplicación de inversas, no solo
  la búsqueda del corte. Mediana y p95 son diagnósticos, no el criterio de pase.
- El consumo de pergamino no es una acción contada por P1 §2.11. La aclaración
  de 004 introduce un ordinal de línea separado y no puede cambiar esa regla.
- Replay y carga dependen de versiones compatibles de cripta/catálogo; errores
  deben preservar el estado activo y no exponer resultados parciales.
- Contraste documental, receptor separado y formato v4 aprobados y registrados
  el2026-11-10. La validación visual automatizada no sustituye el recorrido
  manual humano pendiente de T033.

## Project Structure

### Documentation

```text
specs/004-linea-de-tiempo/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/interfaces.md
└── tasks.md                 # lo genera speckit-tasks
```

### Source code

```text
src/
├── controller2/linea_tiempo.py       # deltas, cortes, checkpoints y truncamiento
├── controller2/fachada.py            # emisión/transición C2 (solo tras aprobar contrato)
├── controller1/savegame.py           # nueva versión y validación binaria
├── controller1/cli.py                # --hasta y --checkpoint-cada
├── orchestrator/sesion.py            # ciclo, consultas puras, replay/carga
├── orchestrator/consola.py           # comando y resumen común
└── main.py                           # salida de replay sin vista

tests/
├── test_linea_tiempo.py              # modelo temporal y checkpoints
├── test_fachada.py                   # eventos, undo y límites C2
├── test_sesion.py                    # consulta, comandos y replay
├── test_savegame.py                  # v4, corrupción y compatibilidad
└── test_gamelog.py                   # replay hasta t
```

**Structure Decision**: capacidad interna de la aplicación existente, sin cuarto
proyecto ni servicio nuevo. La línea reside en C2, `Sesion` presenta el contrato
y C1 trata los bytes; C1/C2 conservan su independencia.

## Constitution Check (post-design)

| Principio | Resultado tras diseño |
| --- | --- |
| Cumplimiento oficial | **Pasa como diseño contrastado**: fuente P2 disponible; implementación y aceptación ejecutada pendientes. |
| Separación/contratos | **Pasa**: receptor y formato v4 aprobados; enmienda004 registrada. |
| Estructuras/evidencia | **Pasa**: lista cronológica y búsqueda binaria propia; rendimiento queda pendiente de benchmark. |
| Determinismo/compatibilidad | **Pasa**: orden causal definido, nuevo formato y rechazos explícitos especificados. |
| Validación | **Pasa como diseño**: offline, replay y carga candidata; ejecuciones pendientes. |
| Spec Kit/trazabilidad | **Pasa** para plan; tasks.md ya existe. La revisión inicial detectó la discrepancia entre receptores002/004; se concretaron y aprobaron interfaces antes del código. |
| Registro LLM | **Pasa**: prompt resumido y uso registrados en `PROMPTS_LLM.md`. |

No hay violaciones deliberadas que requieran excepción; la tabla Complexity
Tracking queda vacía.

## UI/UX de historia — solicitud del usuario, 2026-11-10

La entrega incluye un panel gráfico de historia, además de consola y replay.
Antes de implementarlo, revisar `src/view/app.py`, `ui.py`, `medidas.py`,
`paleta.py`, `texto.py`, `entrada.py` y los paneles/pantallas existentes. Reutilizar
componentes, sprites, convenciones de botones, tipografía y gestión del foco.

Composición prevista: cabecera «Historial de la partida» con tiempo/acción y
etiqueta de consulta histórica; navegación anterior/siguiente y selector de
tiempo o acción; detalle dividido en estadísticas, inventario/efectos, enemigos
locales y mapa conocido histórico. Diferenciar selección histórica del presente.
No incorporar una acción de restaurar al consultar. Incorporar acceso visible
y ayuda contextual; elegir atajo solo después de comprobar los existentes.

Usar tokens compartidos de8/16/24/32 px lógicos para separaciones, padding,
márgenes; mantener esquinas rectas y convertirlos con `Medidas.px` para la escala de la ventana.
El grosor del trazo puede ser1/2 px lógicos para conservar legibilidad: no se
interpreta la retícula como obligación de dibujar contornos de8 px. Conservar
la jerarquía tipográfica existente. Evitar constantes de estilo nuevas dispersas.
La revisión de consistencia no autoriza rediseñar pantallas ajenas a004.

Teclado y ratón deben permitir navegación, selección, consulta y cierre con foco
visible. El panel captura entrada y suspende movimiento y avance automático;
cerrarlo devuelve control sin ejecutar pasos acumulados. Contenido extenso usa
scroll y ajuste de texto sin ocultar controles. Identificar estados vacíos y
errores mediante texto/iconos además de color; conservar la última consulta
válida cuando haya error. Vista consume únicamente DTO de Sesión.

Validar selección histórica y mapa pasado con pruebas de interacción; revisar
capturas a1024×800 y otros tamaños admitidos, nombres largos y listas extensas,
y ejecutar recorrido manual. No confundir renderizado headless con validación
manual. La consola conserva el mismo contenido semántico del resumen.

## Ajuste de implementación validado — 2026-11-10

La auditoría encontró que las inversas P1 son incompletas para historia004.
Se conserva PilaDeshacer y se añade un diario de escrituras observable en los
modelos C2: asignaciones y cambios en listas/mapas producen deltas antes/después
con ruta y presencia. Las listas de longitud variable guardan solo el segmento
reemplazado. No se guarda una copia completa por acción. Los checkpoints y las
consultas normalizan JSON sin referencias al motor; los cortes temporales y de
acción conservan el orden causal mediante posiciones del diario. El formato
v4 transporta este diario, sus cortes y checkpoints.

La observación de conocimiento usa una proyección actual normalizada para
calcular deltas, sin almacenar una proyección completa por acción. Es un costo
de captura dependiente del mapa conocido que debe reevaluarse con cargas
grandes; los tiempos de consulta se publican con el tamaño de estado medido.
Las consultas reconstruyen desde el checkpoint posterior o el estado actual
y aplican los deltas inversos sobre una copia aislada. Las escrituras se
preparan antes de publicarse; fallos inyectados de captura/cierre, incluido
pergamino, restauran estado y rama sin snapshot de transacción.

La interfaz se implementó en src/view/historia.py con tokens compartidos en
medidas.py, paleta existente, sprites y topología histórica cacheada. La
validación visual headless se distingue del recorrido humano pendiente en T033.
