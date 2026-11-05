# Constitución de CRIPTA

## Principios fundamentales

### I. Cumplimiento del enunciado

El equipo DEBE cumplir las reglas oficiales y restricciones académicas de
`docs/enunciado.md`. Las especificaciones DEBEN identificar los requisitos que
satisfacen. Esta constitución no sustituye el enunciado ni autoriza excepciones.
No se DEBEN inventar requisitos funcionales de parte 2: su alcance específico
requiere documentación del curso. Ante contradicciones esenciales no resueltas
por una enmienda explícita, se DEBE registrar el conflicto y solicitar aclaración
antes de implementar la decisión afectada. Las enmiendas existentes de
`CONTRATOS.md` deben leerse junto con sus acuerdos originales, no aisladamente.

### II. Separación de responsabilidades y contratos

C1 DEBE ocuparse de datos, red y persistencia; C2 del motor y las reglas;
el orquestador de coordinar ambos; y la vista de presentar estado y enviar
intenciones mediante Sesión. C1 y C2 NO DEBEN importarse mutuamente. La vista
NO DEBE acceder directamente al API ni a C1. Los contratos compartidos y la
inyección de dependencias DEBEN preservar estas fronteras.
Un cambio de contrato DEBE seguir el acuerdo existente: propuesta escrita,
aceptación del compañero afectado y actualización de `CONTRATOS.md` (regla 6.3).
Esto evita que una modificación local rompa otra capa sin coordinación.

### III. Estructuras y algoritmos justificados

Las estructuras y algoritmos evaluados DEBEN implementarse conforme al enunciado,
sin sustituirlos por implementaciones prohibidas. Las decisiones correspondientes
DEBEN documentar en `DECISIONES.md` el problema, alternativas, elección,
complejidad, evidencia pertinente y límites. Los cambios de rendimiento DEBEN
justificarse con mediciones reproducibles. Las decisiones actuales pueden
revisarse con evidencia; sus detalles accidentales no constituyen obligaciones
permanentes. No se DEBEN extender prohibiciones a usos permitidos por el enunciado.

### IV. Reproducibilidad y compatibilidad explícita

Los cambios DEBEN preservar el determinismo del motor para las mismas entradas,
semilla y versiones compatibles, incluyendo reloj virtual, desempate de eventos,
replay y coherencia de deshacer. Las esperas de red no DEBEN avanzar el reloj
virtual. Deshacer DEBE respetar los intervalos y exclusiones del enunciado y no
usar copias completas del estado.
Los cambios de guardado, bitácora o contratos DEBEN declarar impacto de versión,
compatibilidad y estrategia de migración o rechazo explícito cuando no exista
compatibilidad. No se DEBEN aceptar incompatibilidades silenciosamente.

### V. Validación proporcional y comprobable

Las modificaciones funcionales DEBEN tener pruebas pertinentes al comportamiento
y contratos afectados. Las correcciones DEBEN incluir regresiones cuando sean
reproducibles mediante pruebas; cualquier omisión debe justificarse. Se DEBEN
priorizar pruebas offline con proveedores falsos o sintéticos, sin depender del
servicio HTTP. Las integraciones que requieran red DEBEN distinguirse de ellas.
Las afirmaciones de rendimiento DEBEN indicar carga, método y límites de medición.
No se exige TDD, cobertura del 100 % ni aprobación individual de cada prueba.
Los cambios exclusivamente documentales requieren verificación de consistencia,
no pruebas artificiales del código sin cambios.

### VI. Desarrollo guiado por especificaciones

Las nuevas funcionalidades de parte 2 DEBEN seguir el flujo de GitHub Spec Kit:
especificación, aclaraciones necesarias, plan, tareas, análisis de consistencia
e implementación validada. Los requisitos DEBEN enlazarse con tareas y evidencia
de aceptación. Cada plan DEBE revisar el cumplimiento de esta constitución y
explicitar conflictos antes de implementar. Correcciones menores y documentación
pueden usar un flujo reducido si registran su objetivo, validación y motivo de
la reducción; no requieren generar artefactos sin utilidad.

### VII. Uso responsable y trazable de Codex

Codex se usará como apoyo para parte 2, con revisión y verificación del equipo,
que conserva la responsabilidad por el código y los textos. El uso de LLM DEBE
registrarse conforme a §10.3 en `PROMPTS_LLM.md`: fecha, modelo, prompt y uso de la
respuesta, identificando las paráfrasis según el formato existente. No se DEBEN
incluir credenciales ni atribuir pruebas o mediciones que no se ejecutaron.
Cuando el alcance autorizado impida actualizar la bitácora, el registro pendiente
DEBE declararse y completarse antes de la entrega académica.

## Restricciones tecnológicas y académicas

- La base confirmada es Python 3.11 o superior, con dependencias en
  `requirements.txt`, interfaz Pygame y pruebas con pytest.
- Las restricciones de §7 aplican a los problemas evaluados de §4: se DEBEN usar
  estructuras propias. No se DEBE usar `dict` como índice, caché o tabla de
  búsqueda para resolverlos ni bibliotecas que sustituyan las estructuras exigidas.
  Se DEBEN conservar las excepciones que el enunciado permite para procesamiento
  JSON y otros usos ajenos a esos problemas.
- No se permite `list.sort()` ni `sorted()` en los ordenamientos evaluados;
  tampoco copias completas del estado para resolver el retroceso.
- El acceso HTTP DEBE respetar identificación por ejecución, presupuesto,
  versiones y reintentos del enunciado. Offline no consume solicitudes HTTP.
- GitHub DEBE operarse exclusivamente mediante `git` y `gh` locales. Antes de
  una operación remota autenticada se DEBE comprobar que la identidad efectiva
  sea `EddieBeru`, sin inferirla de la configuración de autor de Git. No se DEBEN
  usar conectores ni MCP de GitHub, ni modificar conexiones automáticamente.
  Ante fallos de autenticación o red, se DEBE informar y preparar comandos para
  ejecución manual; no recurrir al conector.
- `@v1.0.0` identifica la base del producto y NO DEBE moverse. La versión de esta
  constitución es independiente de las versiones del producto y sus formatos.

## Flujo de trabajo y criterios de finalización

Un cambio se considera terminado cuando sus requisitos y criterios de aceptación
están satisfechos; la validación pertinente tiene resultados registrados; y la
documentación, decisiones, contratos y bitácora de LLM están actualizados cuando
corresponda. Se DEBEN declarar fallos, verificaciones no ejecutadas y limitaciones.
La revisión DEBE comprobar fronteras entre capas, restricciones académicas,
reproducibilidad y compatibilidad afectadas por el cambio.

La base de verificación existente es `python -m pytest tests/ -q`; los cambios
localizados pueden validarse primero con las pruebas pertinentes. Las afirmaciones
de rendimiento requieren `python -m src.main --bench` o una medición equivalente
justificada, sin dependencia de la red. No se exige ejecutar benchmarks para
cambios sin impacto de rendimiento.

## Gobernanza

Esta constitución rige las decisiones de desarrollo de parte 2 junto con el
enunciado, los contratos vigentes y las instrucciones aplicables del repositorio.
No transforma decisiones históricas ni propuestas de Codex en requisitos oficiales.
Los requisitos académicos confirmados proceden del enunciado; el flujo Spec Kit y
los criterios de proceso aquí establecidos son acuerdos adoptados por instrucción
del usuario. El alcance funcional específico de parte 2 sigue pendiente de su
enunciado y no queda definido por este documento.

Las enmiendas DEBEN presentar por escrito motivo, reglas afectadas, impacto y
transición necesaria; obtener aprobación explícita del equipo; actualizar este
archivo y revisar la coherencia de los artefactos dependientes. Los cambios de
contratos conservan además su procedimiento propio. No se pueden exceptuar
restricciones académicas mediante una enmienda interna.

Se DEBE aplicar versionado semántico: MAJOR para eliminaciones o redefiniciones
incompatibles de principios; MINOR para principios o guía material nueva; PATCH
para aclaraciones sin cambio normativo. Cada enmienda DEBE conservar la fecha de
ratificación y actualizar la de modificación. La adopción inicial es 1.0.0 porque
el documento anterior solo contenía la plantilla sin normas aprobadas.

**Versión**: 1.0.0 | **Ratificada**: 2026-11-04 | **Última modificación**: 2026-11-04
