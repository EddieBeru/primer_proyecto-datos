# Contratos propuestos: Línea de tiempo (004)

Aprobados explícitamente por el usuario el2026-11-10: «apruebo».
Enmienda registrada en CONTRATOS.md; implementación y validación pendientes.

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

## Propuesta concreta para T002/T003 — 2026-11-10

Aprobación explícita registrada el2026-11-10; véase enmienda004 de CONTRATOS.md.
La implementación de002 se conserva: su receptor opcional
`registrar_cambios(contexto, lote)` / `truncar_ultimo_intervalo()` continúa
recibiendo únicamente conocimiento. El receptor004 será otro argumento opcional
`receptor_historia`, con las firmas propuestas arriba: no se sustituyen métodos
ni se cambia el tipo de los lotes002.

- `registrar_cambio(contexto, inversa)`: registro propio de004, con copia de los
  campos mutables del delta, sin conservar referencias al motor. La captura
  incluye las mutaciones que no cubre el undo P1 (por ejemplo pergaminos), RNG,
  agenda, reloj y estado de fin. No reutilizar ciegamente la inversa P1.
- `cerrar_accion(contexto, estado)`: se invoca tras el drenaje y sincronización;
  crea checkpoint solo al completar K acciones. Eventos intermedios conservan
  cortes propios para consultas por tiempo, sin copias completas por evento.
- `truncar_intervalo(contexto)`: recorta únicamente el sufijo revertido y sus
  checkpoints. El consumo del pergamino queda como delta de la nueva acción,
  conservando las exclusiones y el tope cinco de P1.
- Atomicidad: el receptor es interno, sin E/S ni callbacks de terceros. Se
  preparan y validan los registros antes de publicarlos; si falla el cierre,
  se descartan los registros pendientes y se restauran las mutaciones mediante
  los deltas completos del intervalo, incluidas agenda y RNG. No se permiten
  errores ignorados, historia parcial ni snapshots por acción para rollback.
  Esta garantía debe probarse mediante fallos inyectados antes de aceptar T017.

### Layout v4 y transición

Conservar `MAGIA`, byte de versión, índice de salas y blobs de sala de v3;
versión4 mantiene entradas de índice `<qqq>` (ID/offset/longitud de64 bits).
El core JSON añade `historia`, con versión interna1, K, ordinal vigente,
registros cronológicos, cortes y checkpoints con sus posiciones de registro.
No serializar proveedores, continuación de viaje ni objetos vivos.

C1 reconoce y transporta el bloque; C2 valida tipos exactos, orden causal,
referencias, rangos e intervalos de checkpoints y coherencia con el estado
actual. Sesión instala solo después de validar el candidato completo, sin
modificar partida/viaje en un rechazo. Guardar/cargar mediante004 requiere v4;
v1/v2/v3 se rechazan explícitamente. Los lectores técnicos legados permanecen
separados, sin habilitar carga silenciosa en juego. La selección de K por
defecto sigue pendiente de las mediciones T025/T026.

## Presentación gráfica de004 — solicitud del usuario, 2026-11-10

Vista consulta `Sesion.historia(t)` / `historia_accion(k)` y presenta el DTO en
un panel visual con navegación y detalle jerarquizado; no accede al motor ni
reconstruye historia. Reutiliza paleta, medidas, fuentes y recursos existentes.
El panel recibe foco, bloquea movimiento y pasos automáticos mientras está
abierto, y se cierra con Escape o control visible. La retícula base es8 px
lógicos para espaciados, padding y radios, escalados mediante Medidas.
Esta solicitud de presentación está autorizada por el usuario; no constituye
aprobación implícita de T002/T003 ni cambia todavía CONTRATOS.md.
