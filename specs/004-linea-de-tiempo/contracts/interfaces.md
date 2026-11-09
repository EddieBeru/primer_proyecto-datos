# Contratos propuestos: Línea de tiempo (004)

Estos contratos son propuesta para revisión antes de modificar interfaces
compartidas. No alteran aún `CONTRATOS.md` ni el código.

## Consola

- `historia <t>` consulta el estado antes de la primera decisión en el tiempo
  virtual entero `t`, después de eventos automáticos con reloj ≤t.
- `historia #<k>` consulta el estado inmediatamente anterior a la acción `k`
  (ordinal vigente, desde 1).
- Ambas formas imprimen el mismo resumen y no ejecutan una intención, drenaje,
  avance de reloj, append de bitácora ni cambio en la pila P1.
- Tiempo futuro, tiempo negativo/no entero y ordinal inexistente producen error
  legible sin modificar la partida.

## Sesión

Propuesta de API:

```python
sesion.historia(t: int) -> ResumenHistorico
sesion.historia_accion(k: int) -> ResumenHistorico
```

El DTO contiene los campos de FR-LIN-03 y colecciones inmutables/copias. Ningún
campo expone `EstadoPartida`, entidades vivas, Agenda ni el objeto del proveedor.
El error de rango usa una excepción de validación ya traducida a mensaje amable
por consola y replay.

## Captura desde C2

Propuesta de receptor inyectable independiente de C1:

```python
registrar_cambio(contexto, inversa) -> None
cerrar_accion(contexto, estado) -> None
truncar_intervalo(contexto) -> None
```

`contexto` declara reloj, fase, orden causal y ordinal de línea. C2 emite los
deltas de cada evento a medida que los genera; Sesión señala el fin de la acción
después del drenaje para aplicar el límite K y crear checkpoints. `truncar_intervalo`
quita de la línea los cambios revertidos, manteniendo P1 aparte. La implementación
debe garantizar que un fallo del registrador no deje al motor parcialmente mutado;
la estrategia de error/atomicidad se cierra en tareas antes de cambiar el contrato.

## CLI y replay

- `--checkpoint-cada K`, entero ≥1, establece K para una sesión nueva; si se
  omite, usa el default medido y documentado.
- `--replay RUTA --hasta T` reproduce sin crear `VistaApp` e imprime el resumen
  con el mismo formato que `historia T`.
- Si T excede el reloj final, replay imprime el resumen final y una nota de que
  la partida terminó antes. Un replay inválido conserva sus errores actuales.

## Guardado

- El nuevo formato incluye la línea completa, K, entradas y checkpoints.
- Se propone versión binaria v4, pendiente de inspección de layout y aceptación
  en `CONTRATOS.md` antes de implementación.
- El flujo P2 rechaza explícitamente v1/v2 P1 y v3 P2 anterior a 004, que no
  contienen la línea completa. Lectores técnicos antiguos solo se preservan si
  no hacen que el flujo de juego cargue esos formatos silenciosamente.
