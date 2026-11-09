# Research: Línea de tiempo (004)

## Estado de fuentes

- `specs/004-linea-de-tiempo/spec.md` es la fuente funcional de este plan.
- La guía de Parte II resume la capacidad; el enunciado íntegro P2 no está disponible en el repositorio. No se atribuyen al enunciado oficial las decisiones de la guía ni se cierra aceptación académica sin contraste.
- La implementación parte de la base existente en la rama `main`; `specs/004-linea-de-tiempo` es carpeta de capacidad, no una rama Git dedicada.

## Decisiones

### Reconstrucción histórica con deltas inversos y checkpoints

**Decisión**: reutilizar las entradas inversas de C2 como cambios históricos cronológicos, y conservar checkpoints completos separados por K acciones aceptadas. Para consultar un punto anterior, trabajar sobre una copia aislada del checkpoint posterior más cercano y aplicar las inversas en orden inverso hasta el corte solicitado. Conservar un checkpoint inicial y crear los siguientes al cerrar cada intervalo de K acciones.

**Evidencia local**: `src/controller2/deshacer.py` ya modela cambios reversibles por evento y `aplicar_inversa(estado, agenda, inversa)` restaura C2 sin copiar el estado por acción. `src/controller2/fachada.py` concentra `Fachada._apilar` para registrar inversas y `Fachada.deshacer` para truncar el último intervalo. `EstadoPartida.a_dict()/desde_dict()` serializa el estado requerido por un checkpoint. Las inversas existentes solo alimentan una pila limitada a cinco intervalos, así que la línea necesita su propio almacenamiento sin ese límite.

**Alternativas consideradas**:

- Copia completa por acción: descartada porque contradice FR-LIN-10 y hace crecer memoria según tamaño del estado por acción.
- Reproducir desde el inicio para cada consulta: descartada porque no garantiza como máximo K acciones de reconstrucción ni el límite de 50 ms.
- Guardar solo el último estado y deltas hacia delante: no basta para consultas anteriores y no reutiliza la operación inversa ya probada por el motor.

**Condición de diseño**: todas las mutaciones relevantes, incluidos eventos automáticos, deben producir inversas completas y ordenadas. La implementación debe auditar cada ruta de escritura a C2; cualquier mutación que no pase por `_apilar` requiere integración explícita. El conteo de consultas se medirá en acciones jugador, y también se reportará el número de eventos inversos aplicados por intervalo.

La guía oficial de P1 §2.11 excluye el uso/consumo del pergamino del historial reversible y del contador de acciones del juego. La aclaración del jugador para 004 define un ordinal separado de la línea de tiempo: el pergamino cuenta en `historia #k`/K aunque la pila de deshacer de P1 no lo cuente ni revierta su consumo. No cambiar `EstadoPartida.acciones_jugador` ni la semántica P1 para conseguirlo.

### Índice temporal y acciones numeradas

**Decisión**: almacenar los registros en orden de ejecución y etiquetarlos con reloj virtual, fase/orden dentro del instante y ordinal de acción vigente. En la rama vigente, los tiempos son no decrecientes: al usar un pergamino se trunca la rama revertida y se continúa desde el reloj restaurado, por lo que puede repetirse un tiempo pero no se conserva el tramo de reloj futuro eliminado. Mantener los cortes de tiempo en una lista cronológica y resolver el primer punto de decisión en `t` con búsqueda binaria propia; no ordenar los registros ni usar `sorted()`. `historia <t>` queda después de eventos automáticos con tiempo ≤t y antes de la primera decisión del jugador en t; `historia #k` localiza el corte inmediatamente anterior a la acción numerada k. Cada paso de «ir a» y cada uso aceptado del pergamino ocupa su propio ordinal. Al deshacer, se truncan los intervalos revertidos, se renumeran las acciones supervivientes y se agrega el uso del pergamino al final.

**Alternativas consideradas**: usar tiempo como único índice falla cuando se repite tras deshacer; conservar huecos después del retroceso contradice la regla acordada de renumeración; numerar comandos rechazados o consultas contradice FR-LIN-04 y las aclaraciones aceptadas.

### Límite de versión de guardado

**Decisión**: el formato que incluya la línea completa debe distinguirse de v1/v2 P1 y de v3 P2 anterior a 004. La carga P2 de 004 rechazará esos archivos con un error explícito; no sintetizará ni afirmará historia que no está persistida. El número y layout exactos del formato se fijan al diseñar contrato de persistencia, preservando lectores técnicos que aún necesite la suite.

**Evidencia local**: `src/controller1/savegame.py` escribe v3 cuando hay conocimiento P2, expone `cargar_p2()` para validar y permite lectores técnicos de v1/v2. `Sesion.cargar()` prepara un candidato aislado antes de instalarlo, patrón que debe conservarse al validar la historia serializada.

### Integración con replay y consulta

**Decisión**: `Sesion` expone consultas puras por reloj o ordinal y produce un resumen inmutable. El comando `historia` muestra ese resumen sin llamar al camino de intención/drenaje. `--replay ... --hasta t` reutiliza el replay existente, reconstruye la línea vigente y pide el resumen a `Sesion`; si t excede el reloj final, muestra el último estado y la nota de fin anticipado. El replay no crea `VistaApp`.

**Evidencia local**: `src/orchestrator/sesion.py` coordina intención, drenaje, guardado/carga y replay; `src/main.py` deriva `--replay` sin crear la vista. `src/controller1/gamelog.py` conserva líneas opacas y C2 interpreta las acciones.

## Riesgos pendientes para el plan

- Confirmar con pruebas que las inversas capturan todas las mutaciones de eventos, no solo conocimiento ni las acciones cubiertas por el pergamino.
- Guardar/cargar checkpoints e inversas puede aumentar mucho el archivo; el bench deberá medir bytes reales además de tiempo.
- El criterio ≤50 ms aplica al máximo observado de 1 000 consultas tras 100 calentamientos en una partida de 5 000+ acciones con K por defecto. El resultado depende del tamaño del checkpoint y del número de eventos por acción; informar ambos, no solo cantidad de acciones. Mediana y p95 se reportan como diagnósticos.
- El contrato C2–orquestador para el receptor histórico es nuevo y debe revisarse/aprobarse antes de modificarlo, según `CONTRATOS.md` y la constitución.
- El contraste de reglas y referencias de rendimiento con el enunciado íntegro P2 permanece bloqueado por fuente externa ausente.
