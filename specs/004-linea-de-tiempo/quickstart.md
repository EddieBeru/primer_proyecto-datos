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
  y radios, sin exigir8 px de grosor a los contornos.
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
