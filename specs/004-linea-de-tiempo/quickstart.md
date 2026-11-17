# Guía de validación: 004 Línea de tiempo

Usar Python del proyecto y datos offline. La suite no debe activar
`CRIPTA_API_REAL`. Esta guía define verificaciones futuras; no afirma resultados
antes de que se ejecuten.

## Preparación

```bash
.venv/bin/python -m pytest --version
```

Usar `paquete_demo/` para probar el flujo interactivo. Las ramas de retroceso,
eventos con el mismo reloj y 5 000 acciones deben cubrirse con fixtures
sintéticas y cargas sin red.

## Partida interactiva

```bash
.venv/bin/python -m src.main --jugar --offline paquete_demo/ --cripta cripta-ejemplo --checkpoint-cada 20
```

Resultados esperados:

1. Consultar `historia 0` muestra el estado inicial y no altera reloj, bitácora,
   RNG, inventario, mapa conocido ni pila P1.
2. Completar una acción y consultar `historia #1`; el resumen es justo anterior
   a esa acción. Una acción automática de «ir a» cuenta por cada paso.
3. Consultar tiempo futuro, tiempo negativo/no entero, `#0` o una acción no
   existente; cada consulta se rechaza sin efectos.
4. Usar pergamino con varias acciones disponibles: las acciones revertidas ya
   no aparecen; las supervivientes se renumeran desde 1 y el uso aceptado del
   pergamino queda como la siguiente acción de la línea de tiempo. La regla no
   cambia el contador ni las exclusiones del retroceso P1.
5. Verificar dos eventos automáticos con igual t: `historia t` incluye ambos y
   queda antes de la primera decisión del jugador en ese tiempo.
6. Guardar y cargar; consultas históricas antes/después producen el mismo resumen
   y la carga no reanuda acciones ni avance automático.

## Replay

```bash
.venv/bin/python -m src.main --offline paquete_demo/ --replay partida.log --hasta 4
```

El replay imprime los mismos campos que `historia 4` y no crea la vista. Si el
reloj final es menor que 4, muestra el estado final y avisa que la partida
terminó antes. Comparar replay con la consulta interactiva sobre el mismo log.

## Compatibilidad de guardados

Probar un archivo nuevo de formato 004 y luego cargarlo en frío: conserva toda la
línea. Probar guardados v1/v2 P1 y v3 P2 previos a 004: cada uno debe rechazarse
con un error explícito, sin reemplazar la sesión ni cancelar su viaje actual.

## Determinismo, límites y rendimiento

- Repetir una consulta y confirmar igualdad del resumen, reloj, RNG, estado
  activo, `partida.log` y pila P1.
- Medir consultas por tiempo y ordinal con al menos 5 000 acciones y K por
  defecto; ejecutar 100 calentamientos y luego 1 000 consultas cronometradas.
  Reportar tamaño del estado, eventos aplicados, tiempo de reconstrucción,
  mediana, p95 y máximo. Criterio de pase: el máximo observado de esas 1 000
  consultas es ≤50 ms; mediana y p95 son diagnósticos.
- Comparar al menos K=10, K=20 y K=50, además de reconstrucción sin checkpoints;
  reportar memoria de checkpoints y deltas. El default se elige con estos datos,
  no de antemano.
- Confirmar que cada consulta aplica/revierte como máximo K acciones, que la
  memoria adicional sigue cambios + checkpoints, y que el uso de pergamino
  trunca sin recorrer la historia completa.

Comando previsto tras implementar el benchmark:

```bash
.venv/bin/python -m src.main --bench
```

## Estado de preparación — 2026-11-10

T001 completada: enunciado oficial disponible en `docs/Cripta Parte II.md` y
contraste trazado en research.md. T002/T003 siguen pendientes de conciliación
del receptor histórico con la enmienda002 y definición/acuerdo del formato v4.
Las instrucciones y comandos anteriores son verificaciones futuras: no se ha
implementado004 ni ejecutado sus escenarios o benchmarks. Se puede desarrollar
con el motor actual y fixtures offline; la integración con costos/puertas y
cazadores nuevos se verifica cuando A entregue001.

## Validación visual e interacción (pendiente)

- Revisar primero los componentes y atajos actuales; usar paleta, fuentes y
  escala compartidas. Inspeccionar retícula de8 px lógicos en márgenes, padding
  con esquinas rectas y sin exigir8 px de grosor a los contornos.
- Abrir desde el juego y navegar historia con teclado y ratón; comprobar foco
  visible, selección por tiempo/acción, Escape y retorno al juego sin movimiento
  accidental ni pasos de viaje acumulados.
- Comprobar jerarquía visual de estadísticas, inventario, efectos y enemigos;
  mapa correspondiente al pasado, tiempo/acción visibles y distinción del presente.
- Probar historia vacía, ausencia de enemigos/efectos, errores, nombres largos y
  listas extensas. Los errores conservan el último resumen válido.
- Revisar capturas a1024×800 y otros tamaños admitidos, legibilidad, scroll y
  ausencia de superposición/recorte. Registrar por separado capturas headless
  y recorrido manual efectivo. Estas verificaciones aún no se han ejecutado.

## Ejecución y evidencia — 2026-11-10

Implementación funcional disponible. Contratos aprobados por el usuario
(«apruebo») y registrados en CONTRATOS.md. El estado de preparación anterior
queda reemplazado por este corte. El default K es20, elegido con mediciones.

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python -m pytest tests/ -q
```

Resultado: **464 aprobadas, 1 omitida**, 14,39 s. La omisión es la integración
HTTP opcional; no se activó CRIPTA_API_REAL. `git diff --check` y compilación de
los módulos nuevos sin errores. Pruebas004 en `tests/test_linea_tiempo.py`,
`tests/test_historia.py`, `tests/test_cli_historia.py` y `tests/test_vista_historia.py`.

| Requisitos | Evidencia ejecutada |
| --- | --- |
| FR-LIN-01/03/11 | Comparación completa antes de siete decisiones; eventos veneno/quemadura empatados; reconstrucción de sala, RNG, agenda y entidades |
| FR-LIN-02/04/05 | Consultas t/#k, futuro/negativos/tipos inválidos y ausencia de cambios en estado, historia, log y pila |
| FR-LIN-06 | Replay con mismos resúmenes y salida CLI sin vista; tiempo posterior al final muestra estado final y aviso |
| FR-LIN-07 | Retrocesos sucesivos recortan rama, pergamino con ordinal separado y viaje sin reanudación |
| FR-LIN-08/09/10 | K inválido, checkpoints por intervalo y contador observado ≤K; deltas de listas y objetos sin snapshot por acción |
| FR-LIN-12 | Roundtrip v4 normal/en frío, antorcha/entrada/undo con historia; v3 rechazado, lectores v1/v2 conservados, corrupción sin instalar candidato |
| FR-LIN-13/14 | 5.000 acciones reales, tres K y alternativa sin checkpoints, 100 calentamientos +1000 consultas por alternativa; tabla en DECISIONES.md |
| FR-LIN-15/16 | Panel con teclado/clic/foco, queries inválidas conservan resumen; cuatro tamaños, scroll con40 ítems largos; capturas revisadas |

Los seis casos oficiales del Apéndice B están cubiertos por esas pruebas; el
caso7 local de compatibilidad P2 anterior a004 también. Hay pruebas adicionales
de fallo inyectado al capturar/cerrar acciones o pergaminos que verifican
restauración de estado, rama y log sin snapshot de transacción.

### Recorridos offline ejecutados

- CLI real sobre `paquete_demo`: historia0, movimientoE, historia#1, guardar v4
  y salir; código0, archivo creado. Replay real del log con --hasta100: código0,
  resumen correcto y sin Pygame. Transcripción local en `/tmp/004-consola.txt`
  y `/tmp/004-replay.txt`.
- Capturas Pygame con OfflineBackend real tras S/recoger llave/S, revisadas
  visualmente: [1024×800](../../docs/mediciones/004-historia-ui-1024.png) y
  [640×480](../../docs/mediciones/004-historia-ui-640.png). Las pruebas de entrada
  usan eventos pygame, verifican suspensión de movimiento y retorno sin avance
  automático acumulado. La captura muestra sala actual5 detrás del panel y
  sala histórica3 seleccionada, sin confundir ambos estados.
- Benchmark dirigido de004 ejecutado mediante bench_historia() con defaults;
  se integra también en correr_todo/--bench. El agregado completo no se volvió
  a ejecutar porque incluye mediciones002 ya publicadas; se verificó la sección
  nueva con el mismo generador y camino de producción. Informe principal:
  `docs/mediciones/004-historia-motor-2026-11-10.json`.

Estos recorridos son automatizados/headless con inspección visual del agente.
**T033 sigue pendiente del recorrido manual humano**, con ratón/teclado en una
ventana real; no se afirma aceptación humana de la interfaz. El trabajo de001
y la revisión transversal completa§5.6 permanecen fuera del cierre aislado004.

### Commits locales y revisión de preparación

- `8ecc298`: especificación y contratos aprobados antes del código.
- `6fc82e5`: base002 separada para preservar la dependencia existente.
- `76f62f9`: motor histórico, consultas y persistencia v4.
- `bf3a16f`: captura atómica y exclusión de acciones sin cambios.
- `b34baf6`: explorador visual, controles, ayuda y capturas.

### Recorrido del panel — T033 — 2026-11-13

Recorrido headless con ejecutables reales (Sesión sobre `paquete_demo`,
fixture limpia sin enemigos/trampas/oleadas para un historial determinista de
8 acciones: movimientos, recoger, equipar y esperar; reloj inyectado por el
controlador). Transcripción y capturas en `docs/mediciones/004-t033-*`.

- Apertura con H; resumen inicial en la última acción (#8). Navegación con
  ←/→ y con clic en Anterior/Siguiente; foco con Tab.
- Consulta inválida por tiempo (`999999`): error visible «Tiempo histórico
  inválido o futuro.» y el resumen válido anterior se conserva; consulta
  válida por tiempo retorna al instante correcto (T=5000).
- Scroll del detalle con ↑/↓ y rueda; con contenido extenso el máximo de
  desplazamiento es113 y los controles siguen visibles.
- Contenido extenso (nombre de sala de~300 caracteres e inventario de40
  ítems largos, mediante resumen sintético igual que la prueba automatizada):
  el texto se ajusta por líneas sin recortes ni solapes
  ([normal](../../docs/mediciones/004-t033-panel-largo-1024x800.png) y
  [desplazado al final](../../docs/mediciones/004-t033-panel-largo-scroll-1024x800.png)).
- Cierre con Escape y con clic en Cerrar; el panel sale y la partida queda
  intacta: estado (`a_dict`), bitácora, pila de deshacer, reloj, posición,
  sala y viaje automático idénticos antes/después de todo el recorrido.
- Capturas a tamaños admitidos con controles íntegros: [640×480](../../docs/mediciones/004-t033-panel-640x480.png),
  [1024×800](../../docs/mediciones/004-t033-panel-1024x800.png),
  [1280×720](../../docs/mediciones/004-t033-panel-1280x720.png),
  [1600×900](../../docs/mediciones/004-t033-panel-1600x900.png) y
  [1920×1080](../../docs/mediciones/004-t033-panel-1920x1080.png); más la
  captura del error a1024×800. A640×480 los botones Anterior/Siguiente
  envuelven a una segunda fila y la lista de acciones se desplaza.

Omisión igual que el resto del cierre aislado004: es recorrido dirigido
headless con inspección visual del agente, no una partida humana interactiva
con ratón en ventana real; no se declara aceptación humana de la interfaz.

Checklist de calidad existente:16/16 marcados, sin modificar el archivo de
checklist. Su nota histórica sobre ausencia del enunciado está desactualizada;
la fuente normativa y el contraste actual constan en research.md. La revisión
inicial encontró/reconcilió los receptores antes del primer commit de código.
No se hicieron operaciones remotas ni se implementó trabajo de persona A.

## Integración001/002/003 — 2026-11-16

`tests/test_integracion_001_004.py` comprueba costos variables, cazador, checkpoints, reconstrucción, guardado/carga en frío, replay y retroceso con RNG exacto. Cubre además guardado4 previo sin RNG en inversas mediante deltas históricos y acciones sin azar que no retienen snapshot de generador. Guardados con ocupación de salas sin contenido usan5; los demás mantienen4 y los lectores nuevos admiten ambos con historia completa. La localización de actores y los campos de rutas se reconstruyen tras cargar o revertir errores. Capturas actuales compartidas con003 en docs/mediciones/003-reporte/; revisión headless en tres resoluciones, sin atribuir recorrido humano. Suite completa618 aprobadas/1 omitida; --bench global final en curso.
