# Proyecto CRIPTA: Plan de Trabajo del Controlador (2 mitades) y de la Vista

Este documento **complementa** a `vista y flujos api.md`. Aquel explica *qué* ofrece el API, *qué* hay que mostrar en pantalla y *cómo* fluyen los datos. Este explica **quién construye qué, en qué orden, qué necesita del otro, qué debe esperar y a quién se lo entrega**.

Cuando aquí se mencione "Flujo C", "Parte 2-C" o "endpoint 7", se refiere a lo ya definido en el documento anterior.

---

## 0. Cómo leer este documento

### 0.1 Qué significa "Controlador" aquí

En la guía de arquitectura (MVC), el proyecto tiene carpetas `/model`, `/view`, `/controller` y `/adapters`. Para repartir el trabajo, en este documento llamamos **"Controlador"** a **todo lo que NO es pantalla**: es decir, el "cerebro" completo del juego. En la práctica abarca:

| Carpeta | Qué vive ahí |
|---|---|
| `/adapters` | Hablar con el API, guardar y leer archivos |
| `/model` | Reglas del juego y estructuras de datos propias |
| `/controller` | Coordinar el flujo y traducir acciones del jugador |

Esta decisión mantiene el MVC estricto (nada de pantalla mezclado con reglas), pero permite partir el trabajo en dos mitades iguales de grande.

### 0.2 Las tres piezas

| Pieza | Responsable | Cuándo se hace |
|---|---|---|
| **Controlador 1: Datos, Red y Persistencia** | Integrante 1 | Desde el inicio |
| **Controlador 2: Motor del Juego** | Integrante 2 | Desde el inicio, en paralelo |
| **Vista (Pygame)** | Una sola persona | **Al final**, cuando el Controlador esté "en raya" (ver sección 7) |

Esto reemplaza el reparto de vista de la "Parte 5" del documento anterior, que dividía la interfaz entre dos personas. Ahora la vista la hace principalmente una persona y después.

### 0.3 Equivalencia con los bloques de la guía original

| Guía original | En este plan |
|---|---|
| Bloque 1: Infraestructura, Datos y Persistencia | Controlador 1 |
| Bloque 2: Motor de Simulación, Lógica y Acciones | Controlador 2 |

Si prefieren intercambiar quién hace cada mitad, el plan no cambia: solo se cambian los nombres.

### 0.4 Plantilla que usa cada paso

Cada paso de las secciones 3 y 4 se describe con los mismos campos para que sea fácil de revisar:

| Campo | Qué responde |
|---|---|
| **Qué es** | Explicación en palabras simples |
| **Qué se construye** | Lo que debe existir al terminar |
| **Necesita del otro** | Lo que hay que pedirle al compañero antes o durante |
| **Puede avanzar sin esperar** | Lo que se puede hacer mientras llega lo anterior |
| **Entrega a** | A quién y qué se le pasa |
| **Está terminado cuando** | Criterio claro para dar el paso por cerrado |

---

## 1. Mapa general: quién habla con quién

```
                    ┌──────────────────────────────┐
                    │           VISTA              │  (al final, una persona)
                    │  dibuja y lee el teclado     │
                    └──────────────┬───────────────┘
                                   │  solo habla con la FACHADA
                                   ▼
                    ┌──────────────────────────────┐
                    │ FACHADA DEL CONTROLADOR      │  (la dueña es Controlador 2)
                    │ "recibo intenciones,         │
                    │  entrego una foto del estado"│
                    └──────────────┬───────────────┘
                                   │
          ┌────────────────────────┴────────────────────────┐
          ▼                                                 ▼
┌───────────────────────────┐                ┌───────────────────────────┐
│  CONTROLADOR 2: MOTOR     │  pide datos    │  CONTROLADOR 1: DATOS     │
│  reglas, agenda, combate, │ ─────────────► │  red, caché, guardado,    │
│  IA, inventario, deshacer │ ◄───────────── │  bitácora                 │
│                           │  entrega salas │                           │
│                           │  y fichas      │                           │
└───────────────────────────┘                └─────────────┬─────────────┘
                                                           │
                                                           ▼
                                                  API del profe + archivos
```

**Idea central:** el Motor (Controlador 2) **nunca habla con internet ni con archivos**. Siempre le pide a Datos (Controlador 1). Y la Vista **nunca habla con ninguno de los dos directamente**, solo con la Fachada. Gracias a esto cada pieza se puede probar sola.

---

## 2. Fase 0: acuerdos conjuntos (los dos juntos, antes de programar por separado)

Este es el **Hito 1** de la guía ("consenso en las clases base del Modelo y contratos de datos"). Es lo más importante para evitar confusiones después. Dura poco, pero no se salta.

### 2.1 Qué se decide en esta fase

Se acuerdan por escrito **cinco contratos**. Un contrato es un acuerdo simple del tipo: *"yo te entrego X con esta forma; tú me pides Y de esta manera"*.

| # | Contrato | Entre quiénes | Qué dice, en simple |
|---|---|---|---|
| K1 | **Proveedor de datos** | C1 → C2 | Cómo C2 le pide a C1 la ficha de la cripta, una sala lista para jugar y fichas del catálogo |
| K2 | **Guardado y carga** | C2 ↔ C1 | Qué lista de cosas forma "el estado de una partida" y cómo se entrega a C1 para guardarlo, y cómo regresa al cargar |
| K3 | **Bitácora** | C2 → C1 | Cómo C2 anota cada hecho y C1 lo escribe en el archivo de texto |
| K4 | **Errores** | C1 → C2 | Qué tipos de problema puede reportar C1 (sin presupuesto, sin conexión, no existe, servidor ocupado) y cómo se enteran |
| K5 | **Fachada hacia la Vista** | C2 → Vista | Qué intenciones acepta y qué "foto del estado" devuelve |

### 2.2 K1: Proveedor de datos (propuesta para discutir)

C2 solo conoce estas "peticiones" a C1. No sabe nada de endpoints ni de caché:

| Petición de C2 | Qué devuelve C1, en simple | Qué hace C1 por dentro |
|---|---|---|
| "Dame la lista de criptas" | Nombre, salas y dificultad de cada una | Endpoint 1 |
| "Prepárame la cripta X" | La ficha general (sala inicial, salida, llave, presupuesto, inventario máximo, jugador) y deja listo el esqueleto completo | Endpoints 2 y 4, y consulta de versión si hay datos guardados |
| "Dame la sala N lista para jugar" | La sala **ya armada**: nombre, salidas, enemigos con su ficha, objetos con su ficha y trampas con su ficha | Flujo C: contenido (endpoint 5) + catálogo (endpoint 7) + caché |
| "Dame la ficha del id X" | Una entidad del catálogo | Caché primero; si falta, catálogo |
| "¿Cuántas solicitudes quedan?" | Un número | Contador de presupuesto |

**Frase clave:** C2 pide *"sala N lista"* y recibe la sala con todo resuelto. C2 jamás recibe "una lista de ids para que averigüe qué son". Ese trabajo es de C1.

### 2.3 K2: Guardado y carga

Se acuerda **una lista única de lo que forma una partida** (tomada de la lista del Flujo G del documento anterior): id y versión de la cripta, versión del catálogo, sala actual, jugador, inventario en orden, equipo, estado de cada instancia, estado de cada puerta, salas visitadas, agenda pendiente, reloj virtual, presupuesto restante y pila de deshacer.

- **C2 es dueño de los datos** (sabe qué significa cada uno).
- **C1 es dueño del formato en bytes** (sabe escribirlo y leerlo).
- Cualquier dato nuevo que C2 agregue al estado **debe avisarse a C1** (ver regla de cambios en la sección 6).

### 2.4 K3: Bitácora

C2 manda a C1 una línea de texto por cada hecho relevante. Se acuerda **un formato único de línea** (por ejemplo: reloj virtual, tipo de hecho, quién, detalle). El formato es crítico porque `--replay` lo lee de vuelta, y quien lo lee (C2) debe poder entender lo que escribió C1.

### 2.5 K4: Errores

Se acuerda una lista cerrada de "tipos de problema" que C1 puede reportar y cómo debe reaccionar C2:

| Problema | Quién lo detecta | Qué hace C2 |
|---|---|---|
| Servidor ocupado (429) | C1, y lo maneja solo con espera | Normalmente nada: C1 reintenta. Solo se entera si se agotan los intentos |
| Sin conexión | C1 | Avisar a la fachada para mostrar error amable |
| No existe (404) | C1 | Decidir según el caso (sala inexistente = error grave; ficha inexistente = usar objeto genérico) |
| Presupuesto agotado | C1 | Aplicar la decisión del equipo (ver preguntas abiertas) |
| Contenido inválido del servidor (500) | C1 | Error amable, no insistir |

### 2.6 K5: Fachada hacia la Vista

Se acuerda lo mínimo que la vista necesitará. Se detalla en la sección 8, pero **se define ahora** para que C2 construya su motor pensando en ella.

### 2.7 Entregables de la Fase 0

- [ ] Un archivo corto `CONTRATOS.md` en el repositorio con los cinco contratos.
- [ ] Una **lista de clases base del Modelo** (Jugador, Sala, Salida, Enemigo en sala, Trampa en sala, Objeto, Estado de partida) con sus campos.
- [ ] Un acuerdo explícito de **qué valor por defecto** se usa para campos vacíos del API (`cerrada`, `rearme`, `cura`, `vida`, etc.). Mientras el profe no responda, se escribe la suposición y se marca como "pendiente de confirmar".
- [ ] Ramas creadas en GitHub y reglas de revisión de la sección 6.

---

## 3. CONTROLADOR 1: Datos, Red y Persistencia (Integrante 1)

### 3.0 En una frase

C1 es **el encargado de traer, guardar y recordar datos**. Todo lo que implique internet, archivos y memoria de corto plazo (caché) es suyo. Entrega a C2 datos ya limpios y listos.

### 3.1 Estructuras de datos propias que le tocan a C1

| Estructura | Para qué | Nota |
|---|---|---|
| Lista doblemente enlazada | Orden de uso de la caché LRU | Propuesta propia, no la lista nativa |
| Tabla hash propia | Encontrar rápido una ficha por su id | **No se usa `dict`** como índice principal (restricción del proyecto) |
| Mergesort propio | Ordenar puntajes y catálogos | Sin `list.sort()` ni `sorted()`. También lo usará C2 para el inventario |

### 3.2 Pasos de C1, en orden recomendado

#### C1-1: Proveedor de datos **falso** (el primer regalo para C2)

| Campo | Detalle |
|---|---|
| **Qué es** | Una versión de prueba de K1 que **no usa internet**: devuelve datos fijos escritos a mano |
| **Qué se construye** | Un módulo con las mismas peticiones de K1 pero que responde con la cripta de ejemplo (6 salas) y algunas fichas de catálogo de ejemplo |
| **Necesita del otro** | Los contratos de la Fase 0 ya firmados |
| **Puede avanzar sin esperar** | Todo, no depende de nadie más |
| **Entrega a** | **C2**, lo más pronto posible (idealmente en los primeros días) |
| **Está terminado cuando** | C2 puede pedir "prepárame la cripta" y "dame la sala 1 lista" y recibir datos válidos sin conexión |

> **Por qué va primero:** sin esto, C2 se queda esperando a que C1 termine toda la red. Con esto, C2 avanza desde el día uno y después solo se cambia el proveedor falso por el real, sin tocar el motor.

#### C1-2: Cliente HTTP base

| Campo | Detalle |
|---|---|
| **Qué es** | La pieza que hace cualquier petición al API de forma segura |
| **Qué se construye** | Generación única del carné (UUID) al iniciar; envío del carné en toda petición; tiempo límite (timeout) explícito; lectura del código de respuesta; conversión de 400/404/429/500 en los "tipos de problema" de K4 |
| **Necesita del otro** | K4 (la lista de errores) |
| **Puede avanzar sin esperar** | Todo |
| **Entrega a** | Uso interno de C1 (lo usan los pasos C1-3 y C1-4) |
| **Está terminado cuando** | Se puede pedir la lista de criptas (endpoint 1) y se ve la respuesta; y se probó provocar un error (por ejemplo, pedir una cripta inexistente) y llega el 404 como tipo de problema |

#### C1-3: Contador de presupuesto y manejo del 429

| Campo | Detalle |
|---|---|
| **Qué es** | Un contador que descuenta cada petición real, y el reintento automático cuando el servidor pide esperar |
| **Qué se construye** | Contador que arranca con `presupuesto_solicitudes`; descuento por cada petición; lectura de `reintentar_en`; espera sin congelar; número máximo de intentos; aviso de "presupuesto agotado" |
| **Necesita del otro** | Respuesta del profe sobre si los reintentos y las consultas de versión descuentan. **Mientras no responda: contar todo** |
| **Puede avanzar sin esperar** | Todo, con la regla de contar todo |
| **Entrega a** | **C2** (la petición "¿cuántas solicitudes quedan?") y a la **Vista** en modo desarrollo (vía fachada) |
| **Está terminado cuando** | Se probó con un servidor que responde 429 y el programa espera, reintenta y sigue; y se probó agotar el presupuesto y el aviso sale |

#### C1-4: Endpoints de cripta (lista, ficha, versión, esqueleto)

| Campo | Detalle |
|---|---|
| **Qué es** | Las cuatro peticiones relacionadas con una cripta (endpoints 1 a 4) |
| **Qué se construye** | Una función por cada endpoint; para el esqueleto, pedir **todas las páginas** (según `total_paginas`) y unirlas en un plano completo |
| **Necesita del otro** | Las clases base del Modelo (Sala, Salida) de la Fase 0, para saber en qué forma entregar el plano |
| **Puede avanzar sin esperar** | La parte de red; la conversión a clases se hace al llegar las clases base |
| **Entrega a** | Uso interno (lo usa C1-7) |
| **Está terminado cuando** | Con la cripta real se obtiene la ficha y el plano completo, y el número de salas del plano coincide con `salas_total` |

#### C1-5: Endpoints de catálogo (versión, lote, ficha)

| Campo | Detalle |
|---|---|
| **Qué es** | Las tres peticiones del catálogo (endpoints 6, 7 y 8) |
| **Qué se construye** | Petición por lote que: (1) quita ids repetidos, (2) parte en grupos de máximo 10, (3) hace una petición por grupo; petición de ficha única solo para casos sueltos; reconocimiento de las 9 clases de entidad por su campo `clase` |
| **Necesita del otro** | Clases base del Modelo para cada tipo de objeto |
| **Puede avanzar sin esperar** | La parte de red |
| **Entrega a** | Uso interno (lo usa C1-6 y C1-7) |
| **Está terminado cuando** | Se piden 25 ids y el programa hace exactamente 3 peticiones; y un id repetido no provoca error 400 |

#### C1-6: Caché LRU del catálogo (con sus estructuras propias)

| Campo | Detalle |
|---|---|
| **Qué es** | La "memoria de fichas" que evita volver a preguntar lo que ya sabemos |
| **Qué se construye** | Tabla hash propia + lista doblemente enlazada propia; límite `--cache-size`; al usar una ficha se pasa al frente; al llenarse se saca la menos usada; opción de guardar la caché a disco y leerla al arrancar; validación contra la versión del catálogo (Flujo H) |
| **Necesita del otro** | Nada para la estructura; para guardar en disco, el formato lo decide C1 solo |
| **Puede avanzar sin esperar** | Todo. **Las estructuras se pueden construir y probar sin red** |
| **Entrega a** | C1-7 (uso interno) y a **ambos** para las pruebas de rendimiento (`--bench`) |
| **Está terminado cuando** | Hay pruebas que demuestran: orden de desalojo correcto, tamaño nunca excede el límite, y una ficha recién usada no se desaloja primero |

> **Atención:** el desalojo y el orden de uso son lo que más revisará el profe. Documentar el razonamiento para el Documento de Decisiones de Diseño (Hito 3).

#### C1-7: Cargador de salas "listas para jugar"

| Campo | Detalle |
|---|---|
| **Qué es** | El paso que une todo: es el **Flujo C** del documento anterior hecho código |
| **Qué se construye** | La petición "dame la sala N lista": revisa si el contenido ya está guardado; si no, pide un lote de hasta 10 salas (la N más vecinas probables); lista todos los ids necesarios (tipos de enemigos, tipos de trampas, objetos y lo que sueltan los enemigos); revisa la caché; pide al catálogo lo que falte en lotes de 10; arma la sala completa |
| **Necesita del otro** | Las clases de **Sala viva** del Modelo (qué campos espera C2 al recibirla) |
| **Puede avanzar sin esperar** | La mayor parte; si C2 aún no termina las clases, C1 usa las del contrato de la Fase 0 |
| **Entrega a** | **C2** (reemplaza al proveedor falso de C1-1) |
| **Está terminado cuando** | C2 cambia del proveedor falso al real y su motor sigue funcionando sin cambios; y se comprobó que entrar a una sala nueva gasta pocas peticiones (idealmente una de contenido más las de catálogo que falten) |

#### C1-8: Guardado y carga binaria de partida

| Campo | Detalle |
|---|---|
| **Qué es** | Convertir el estado de la partida a un archivo de bytes y viceversa (Flujo G) |
| **Qué se construye** | Un formato binario propio con `struct`; escritura; lectura; validación de que el archivo es válido; comparación de versiones de cripta y catálogo al cargar (endpoints 3 y 6) |
| **Necesita del otro** | **De C2: la lista final de lo que forma el estado** (K2). Esto es una **dependencia fuerte** |
| **Puede avanzar sin esperar** | La estructura del archivo (encabezado, versión del formato, orden de las secciones) y la lectura/escritura de datos simples. Los datos más complejos (agenda, pila) esperan a C2 |
| **Entrega a** | **C2** (guardar y cargar desde el menú de pausa) |
| **Está terminado cuando** | Se guarda una partida a mitad de juego, se cierra el programa, se vuelve a abrir, se carga y **el estado es idéntico** (se verifica comparándolos). También: un archivo dañado produce error amable, no un cierre brusco |

#### C1-9: Bitácora y lectura para `--replay`

| Campo | Detalle |
|---|---|
| **Qué es** | El diario de la partida, solo se agrega al final |
| **Qué se construye** | Escribir una línea por hecho (K3); nunca modificar lo anterior; lectura de vuelta línea por línea; entrega de las líneas a C2 en orden |
| **Necesita del otro** | De C2: el formato exacto de línea y la lista de tipos de hecho (K3) |
| **Puede avanzar sin esperar** | La escritura y lectura de líneas genéricas |
| **Entrega a** | **C2** (para que el motor reproduzca) |
| **Está terminado cuando** | Una partida jugada genera una bitácora y, al reproducirla con `--replay`, el resultado final es el mismo |

#### C1-10: Arranque y banderas de línea de comandos

| Campo | Detalle |
|---|---|
| **Qué es** | Leer lo que el usuario escribe al ejecutar el programa |
| **Qué se construye** | Lectura de `--cache-size`, `--replay`, `--bench`; validación de valores; arranque del carné (Flujo A) |
| **Necesita del otro** | Qué hace C2 con `--replay` y con `--bench` |
| **Puede avanzar sin esperar** | La lectura y validación |
| **Entrega a** | Ambos |
| **Está terminado cuando** | Cada bandera tiene una prueba y un mensaje de ayuda claro |

#### C1-11: Ordenamiento propio (mergesort) y pruebas de rendimiento

| Campo | Detalle |
|---|---|
| **Qué es** | Un ordenamiento hecho por ustedes, sin `list.sort()` ni `sorted()` |
| **Qué se construye** | Mergesort que recibe una lista y un criterio de comparación; pruebas con listas pequeñas, vacías y con repetidos; medidas de tiempo para `--bench` |
| **Necesita del otro** | De C2: qué cosas hay que ordenar (inventario, puntajes) |
| **Puede avanzar sin esperar** | Todo |
| **Entrega a** | **C2** (inventario y puntajes) y al informe de decisiones |
| **Está terminado cuando** | Hay pruebas, y las medidas con listas de tamaños crecientes están guardadas |

### 3.3 Resumen: qué entrega C1 y cuándo

| Entrega | Para quién | Debe estar listo antes de… |
|---|---|---|
| Proveedor falso (C1-1) | C2 | Que C2 empiece su motor (primera semana) |
| Contador de presupuesto (C1-3) | C2 y Vista | Que C2 integre el pedido de salas |
| Cargador de salas (C1-7) | C2 | **Hito 2** (integración) |
| Guardado y carga (C1-8) | C2 | Hito 2 |
| Bitácora y lectura (C1-9) | C2 | Hito 2 |
| Mergesort (C1-11) | C2 | Que C2 ordene inventario y puntajes |

---

## 4. CONTROLADOR 2: Motor del Juego (Integrante 2)

### 4.0 En una frase

C2 es **el que hace que el juego "funcione"**: reglas, turnos, combate, enemigos, inventario, deshacer y victoria. No conoce el internet ni los archivos: pide todo a C1.

### 4.1 Estructuras de datos propias que le tocan a C2

| Estructura | Para qué | Nota |
|---|---|---|
| Cola de prioridad **sobre lista enlazada** | Agenda de eventos | **Acordado** en la guía. Saca el evento con menor tiempo y, si empatan, el de menor número de secuencia |
| Lista doblemente enlazada | Inventario | Recorrido en ambos sentidos, soltar de cualquier posición, equipar = mover al frente |
| Pila (stack) | Historial para deshacer | Guarda la acción inversa, no copias del estado completo; tope de 5 |
| Uso del mergesort de C1 | Ordenar inventario y puntajes | Se pide a C1, no se reescribe |

### 4.2 Pasos de C2, en orden recomendado

#### C2-1: Clases base del Modelo

| Campo | Detalle |
|---|---|
| **Qué es** | Las "fichas" de lo que existe en el juego |
| **Qué se construye** | Jugador, Sala viva, Salida (puerta), Enemigo en sala, Trampa en sala, las 9 clases de entidad del catálogo, Estado de partida |
| **Necesita del otro** | Revisión de C1 (son parte de los contratos de la Fase 0) |
| **Puede avanzar sin esperar** | Todo |
| **Entrega a** | **C1** (para que sepa en qué forma entregar sus datos) |
| **Está terminado cuando** | Los dos las aprobaron y quedan documentadas en `CONTRATOS.md` |

> Distinguir siempre **tipo** (molde del catálogo) de **instancia** (cada enemigo o trampa concreto). El estado cambiante se guarda por instancia (Parte 2-C del documento anterior).

#### C2-2: Agenda de eventos (cola de prioridad con listas enlazadas)

| Campo | Detalle |
|---|---|
| **Qué es** | La "lista de pendientes" ordenada por cuándo ocurre cada cosa |
| **Qué se construye** | Estructura propia; insertar un evento con su tiempo; sacar el más próximo; desempate por número de secuencia (contador que crece con cada evento); poder **quitar** un evento (lo necesitará el deshacer) |
| **Necesita del otro** | Nada |
| **Puede avanzar sin esperar** | Todo. Se puede probar completamente aislada |
| **Entrega a** | Uso interno (C2-3 y siguientes) y a **C1** (lo que contiene la agenda se guarda en la partida) |
| **Está terminado cuando** | Pruebas con empates de tiempo, con inserciones en desorden, con eliminación en medio y con agenda vacía |

#### C2-3: Reloj virtual y turnos por velocidad

| Campo | Detalle |
|---|---|
| **Qué es** | El "paso del tiempo" del juego, que no depende del reloj real |
| **Qué se construye** | Reloj virtual; cálculo de cuándo le toca actuar a cada criatura según su `velocidad`; avance al siguiente evento de la agenda; reglas de determinismo (mismas acciones, mismo resultado) |
| **Necesita del otro** | La regla exacta de cómo se calcula el tiempo entre turnos a partir de la velocidad. **Esto lo define el enunciado del profe, no este documento** |
| **Puede avanzar sin esperar** | La estructura; la fórmula se conecta cuando esté clara |
| **Entrega a** | Uso interno |
| **Está terminado cuando** | Dos criaturas con velocidades distintas actúan en el orden esperado en una prueba controlada |

#### C2-4: Movimiento entre salas y puertas

| Campo | Detalle |
|---|---|
| **Qué es** | Poder ir por N, S, E u O (Flujo E del documento anterior) |
| **Qué se construye** | Reglas de salida existente, puerta cerrada, llave requerida, cierre automático (programa un evento en la agenda); cambio de sala; **petición a C1 de "sala N lista"** al cruzar |
| **Necesita del otro** | **De C1: el proveedor de salas** (al principio el falso, luego el real) |
| **Puede avanzar sin esperar** | Todo con el proveedor falso |
| **Entrega a** | La Fachada (C2-12) |
| **Está terminado cuando** | Con el proveedor falso se recorre toda la cripta de 6 salas, se prueba una puerta cerrada con llave, y se abre con la llave del inventario |

#### C2-5: Inventario (lista doblemente enlazada)

| Campo | Detalle |
|---|---|
| **Qué es** | La mochila del jugador |
| **Qué se construye** | Lista propia; recoger (respetando `inventario_max`); soltar de cualquier posición; equipar (mueve al frente); recorrer hacia adelante y hacia atrás; ordenar con el mergesort de C1 |
| **Necesita del otro** | **De C1: el mergesort (C1-11)** solo para la función de ordenar |
| **Puede avanzar sin esperar** | Todo lo demás |
| **Entrega a** | Fachada y a **C1** (el inventario se guarda en el estado) |
| **Está terminado cuando** | Pruebas con inventario vacío, lleno, soltar el primero, el último y uno del medio, y equipar uno del fondo |

> **Duda abierta:** el API trae `peso` en cada objeto pero solo da un límite por **cantidad** (`inventario_max`). Hay que confirmar si el peso limita algo. Mientras tanto, solo se cuenta cantidad.

#### C2-6: Combate

| Campo | Detalle |
|---|---|
| **Qué es** | Pelear con enemigos y recibir daño |
| **Qué se construye** | Ataque del jugador y de enemigos; aplicación de ataque, defensa y bonus del equipo; muerte de enemigos; objetos que **suelta** el enemigo (se piden a C1 si no estaban listos) |
| **Necesita del otro** | De C1, solo las fichas de lo que sueltan los enemigos (ya vienen en "sala lista") |
| **Puede avanzar sin esperar** | Todo |
| **Entrega a** | Fachada |
| **Está terminado cuando** | Pruebas con enemigo más fuerte, más débil, con mucha defensa y con equipo con bonus |

> **Importante:** la fórmula exacta del daño **no está en el API**. Debe tomarse del enunciado del profe. Aquí no se inventa.

#### C2-7: Trampas, veneno, pociones, antídoto y antorcha

| Campo | Detalle |
|---|---|
| **Qué es** | Todo lo que causa efectos con el paso del tiempo |
| **Qué se construye** | Trampa que hace daño al pisarla y se rearma si trae `rearme`; veneno como evento repetido en la agenda; pociones con `cura`, `modificador_velocidad` y `duracion`; antídoto que quita el veneno; antorcha con su `duracion`; fin de cada efecto como evento de agenda |
| **Necesita del otro** | Nada |
| **Puede avanzar sin esperar** | Todo |
| **Entrega a** | Fachada y estado de partida |
| **Está terminado cuando** | Cada efecto empieza, dura lo debido y termina en el momento correcto; y el antídoto cancela el veneno pendiente |

#### C2-8: Comportamiento de enemigos y rastro

| Campo | Detalle |
|---|---|
| **Qué es** | La "inteligencia" de cada tipo de enemigo |
| **Qué se construye** | **Guardián** (cuida su sala), **errante** (se mueve entre salas), **rastreador** (sigue el rastro fresco del jugador); el "rastro" por sala que se va debilitando con el tiempo |
| **Necesita del otro** | El plano completo de la cripta (viene de C1 en la ficha de la cripta); regla exacta de "frescura del rastro" (enunciado del profe) |
| **Puede avanzar sin esperar** | Guardián y errante; rastreador cuando esté la regla del rastro |
| **Entrega a** | Fachada y estado de partida |
| **Está terminado cuando** | Con una cripta de prueba, cada tipo se comporta distinto y el resultado es **siempre igual** con las mismas acciones |

#### C2-9: Deshacer con pergamino de retroceso

| Campo | Detalle |
|---|---|
| **Qué es** | Volver atrás hasta 5 acciones |
| **Qué se construye** | Pila de acciones inversas; cada acción guarda **qué cambió** (no una copia de todo); al deshacer, también se revierten los eventos de agenda que esa acción creó; el pergamino se consume |
| **Necesita del otro** | Nada; pero **toca todos los demás pasos de C2** (cada acción debe saber su inversa) |
| **Puede avanzar sin esperar** | Todo. **Conviene hacer la base temprano** para que cada acción nueva ya nazca con su inversa |
| **Entrega a** | Fachada y a **C1** (la pila va en el guardado) |
| **Está terminado cuando** | Hacer 6 acciones, deshacer 5 y que el estado coincida con el de la acción 1; y deshacer después de un combate o de abrir una puerta con cierre automático funciona |

#### C2-10: Victoria, derrota y puntaje

| Campo | Detalle |
|---|---|
| **Qué es** | Saber cuándo termina el juego |
| **Qué se construye** | Victoria: estar en `sala_salida` con `llave_salida`; derrota: vida en 0; cálculo de puntaje; lista de puntajes ordenada con el mergesort de C1 |
| **Necesita del otro** | Mergesort de C1; la regla del puntaje (enunciado) |
| **Puede avanzar sin esperar** | La condición de fin |
| **Entrega a** | Fachada |
| **Está terminado cuando** | Hay pruebas de ganar, perder y de intentar salir sin la llave |

#### C2-11: Registro en bitácora y reproducción (`--replay`)

| Campo | Detalle |
|---|---|
| **Qué es** | Anotar cada hecho y volver a jugarlo desde el diario |
| **Qué se construye** | Envío de una línea por hecho a C1 (K3); modo de reproducción que lee las líneas de C1 y las vuelve a ejecutar |
| **Necesita del otro** | **De C1: escritura y lectura de bitácora (C1-9)** |
| **Puede avanzar sin esperar** | El formato de las líneas y la forma de "traducir línea a acción" |
| **Entrega a** | Ambos (prueba conjunta) |
| **Está terminado cuando** | Una partida y su reproducción terminan en estados idénticos |

#### C2-12: Fachada hacia la Vista

| Campo | Detalle |
|---|---|
| **Qué es** | La "ventanilla" con la que la Vista conversa con todo el Controlador |
| **Qué se construye** | Recepción de intenciones (moverse, atacar, equipar, soltar, recorrer, deshacer, pausa, guardar, cargar); entrega de una **"foto del estado"** (qué mostrar ahora); entrega de mensajes nuevos de la bitácora; entrega de avisos de error amable |
| **Necesita del otro** | De C1: estado del presupuesto y errores de red |
| **Puede avanzar sin esperar** | Todo |
| **Entrega a** | **La Vista** (al final) |
| **Está terminado cuando** | Un programa de prueba en consola puede jugar una partida completa **usando únicamente la fachada** (ver sección 7) |

### 4.3 Resumen: qué entrega C2 y cuándo

| Entrega | Para quién | Debe estar listo antes de… |
|---|---|---|
| Clases base (C2-1) | C1 | Que C1 convierta datos reales en clases |
| Lista del estado de partida (parte de K2) | C1 | Que C1 termine el guardado |
| Formato de línea de bitácora (K3) | C1 | Que C1 termine la bitácora |
| Agenda, inventario y pila (C2-2, 5, 9) | C1 | Se guardan en la partida |
| Fachada (C2-12) | Vista | Inicio de la vista |

---

## 5. Matriz de dependencias entre las dos mitades

### 5.1 "¿Qué necesito del otro?" (lectura rápida)

| Quién espera | Qué espera | De quién | Mientras espera, puede… |
|---|---|---|---|
| C2 (motor) | Proveedor falso | C1 | Nada; por eso C1 lo entrega primero |
| C2 | Proveedor real de salas | C1 (C1-7) | Seguir con el falso |
| C2 | Contador de presupuesto | C1 (C1-3) | Usar un número fijo de prueba |
| C2 | Mergesort | C1 (C1-11) | Construir todo el inventario excepto "ordenar" |
| C2 | Guardado y carga | C1 (C1-8) | Todo lo demás |
| C2 | Escritura y lectura de bitácora | C1 (C1-9) | Escribir en una lista en memoria para probar |
| C1 | Clases base del Modelo | C2 (C2-1) | Construir red y estructuras de caché |
| C1 | Lista de lo que forma el estado | C2 | Estructura general del archivo |
| C1 | Formato de línea de bitácora | C2 | Escritura y lectura de texto genérico |
| C1 | Qué ordenar y con qué criterio | C2 | Mergesort con criterio general |

### 5.2 Puntos donde **cada uno puede bloquear al otro** (atención especial)

| Riesgo | Quién bloquea a quién | Cómo se evita |
|---|---|---|
| Sin proveedor falso, C2 no puede probar nada | C1 → C2 | C1-1 va **primero** |
| Cambiar el estado de partida sin avisar rompe el guardado | C2 → C1 | Regla de cambios (sección 6.3) |
| Cambiar el formato de bitácora rompe `--replay` | Ambos | Formato fijo desde la Fase 0 |
| La fórmula del daño o del tiempo no está clara | Ambos | Se resuelve con el enunciado o preguntando al profe temprano |
| Pila de deshacer añadida al final obliga a reescribir todas las acciones | C2 → C2 | Construir la base del deshacer temprano |

---

## 6. Reglas de comunicación y transparencia

### 6.1 Ramas y revisión

- Una **rama por paso** (por ejemplo `c1-cache-lru`, `c2-agenda`).
- Todo cambio entra por **Pull Request**.
- **Cada PR lo revisa el otro integrante.** Así los dos entienden las dos mitades.
- Un PR que toca un contrato (sección 2) debe decir **"toca contrato K#"** en el título.

### 6.2 Nota de entrega (la plantilla para decir "ya terminé")

Cada vez que un paso se cierra, quien lo hizo deja esta nota en el PR o en un archivo `ENTREGAS.md`:

```
PASO: C1-7 Cargador de salas
ENTREGO A: C2
QUÉ PUEDE USAR: función "sala_lista(n)" que devuelve una sala armada
CÓMO PROBARLO: ejecutar prueba_sala_lista (en tests/)
LÍMITES CONOCIDOS: aún no precarga vecinas; cache-size mínimo 20
CAMBIOS A CONTRATOS: ninguno
```

La nota evita preguntar "¿ya puedo usarlo?" y deja registro para el Documento de Decisiones de Diseño.

### 6.3 Regla de cambios a contratos

1. Quien quiere cambiar un contrato **lo propone por escrito** (en una incidencia o en el PR).
2. El otro responde **sí, no o cambio esto**.
3. Hasta que haya respuesta, **no se programa sobre el cambio**.
4. Se actualiza `CONTRATOS.md` en el mismo PR.

### 6.4 Puntos de sincronización fijos

| Momento | Qué se revisa | Quiénes |
|---|---|---|
| Fin de la Fase 0 | Contratos firmados | Ambos |
| Cuando C1 entrega el proveedor falso | C2 confirma que funciona | Ambos |
| Cuando C1 entrega el proveedor real | C2 cambia el proveedor y corre sus pruebas | Ambos |
| Fin de las dos mitades (Hito 2) | Una partida completa de punta a punta (sin vista) | Ambos |
| Antes de empezar la Vista | Revisar el criterio de la sección 7 | Ambos + persona de la vista |
| Hito 3 | `--bench` y Documento de Decisiones de Diseño | Ambos |

### 6.5 Registro de decisiones

Un archivo `DECISIONES.md` donde cada decisión importante se anota en 3 líneas: **qué se decidió, por qué y qué alternativa se descartó.** Es la base del Documento de Decisiones de Diseño que se entrega en el Hito 3.

---

## 7. Cronograma por fases y criterio "Controlador en raya"

### 7.1 Fases

| Fase | C1 (Datos) | C2 (Motor) | Juntos |
|---|---|---|---|
| **0** | Revisa contratos | Propone clases base | Contratos, ramas, repositorio (Hito 1) |
| **1** | C1-1 proveedor falso, C1-2 cliente HTTP, C1-3 presupuesto y 429 | C2-1 clases base, C2-2 agenda, C2-3 reloj virtual | Revisión cruzada de PRs |
| **2** | C1-4 y C1-5 endpoints, C1-6 caché LRU, C1-11 mergesort | C2-4 movimiento y puertas, C2-5 inventario, C2-6 combate | C2 pasa a usar el proveedor real cuando C1 lo entregue |
| **3** | C1-7 cargador de salas, C1-8 guardado, C1-9 bitácora | C2-7 efectos, C2-8 enemigos, C2-9 deshacer | **Hito 2**: partida completa en consola |
| **4** | C1-10 banderas, pruebas de rendimiento | C2-10 fin de juego, C2-11 replay, C2-12 fachada | Prueba `--bench`, `--replay` y guardado |
| **5** | Apoya a la Vista (preguntas sobre datos) | Apoya a la Vista (preguntas sobre la fachada) | Hito 3 y documento de decisiones |
| **6** | **Vista** (una persona; ver sección 8) | | |

> **Nota de diseño:** la vista se deja "al final" para el **trabajo de la vista**, pero no es obligatorio dejar a la otra persona ociosa: puede dedicarse a pruebas, `--bench`, documento de decisiones y revisión.

### 7.2 Herramienta puente: la consola de pruebas

Mientras la vista no existe, el equipo usa un **programa de consola** que:

- imprime la "foto del estado" de la fachada como texto;
- lee comandos escritos (por ejemplo "norte", "atacar", "equipar 2");
- usa **únicamente la fachada**, igual que lo hará la vista.

**Quién la construye:** C2 (porque es la dueña de la fachada), en una versión mínima. **Para qué sirve:** probar el Controlador completo y comprobar que la fachada tiene todo lo que la vista necesitará. La guía permite consola o Pygame, así que esta consola también sirve como plan B.

### 7.3 Criterio "Controlador en raya" (la puerta de entrada a la Vista)

La Vista **no empieza** hasta que se cumplan estas condiciones:

- [ ] Se juega una partida completa (inicio → victoria) desde la consola de pruebas, **con la cripta real del API**.
- [ ] Se juega una partida completa que termina en derrota.
- [ ] Guardar, cerrar, cargar y continuar funciona.
- [ ] `--replay` reproduce una partida y termina en el mismo resultado.
- [ ] El deshacer funciona tras combate, apertura de puerta y recogida de objeto.
- [ ] El manejo del 429 y del presupuesto agotado muestra mensajes claros, sin cierre brusco.
- [ ] La caché respeta `--cache-size` y está probada.
- [ ] Hay pruebas automáticas para agenda, caché, inventario y pila.
- [ ] Los contratos (`CONTRATOS.md`) están al día y la fachada está **congelada** (cambios solo con regla 6.3).
- [ ] Ambos pueden explicar **cualquier** parte del Controlador (no solo la suya).

Si falta algo, **no se pasa a la vista.** Es mucho más caro arreglar el motor mientras se dibuja encima.

---

## 8. VISTA (al final, mayormente una persona)

### 8.1 Quién la hace y quién ayuda

| Rol | Responsable | Qué hace |
|---|---|---|
| **Persona de la Vista** | Una de las dos (la que termine primero, o la que prefieran) | Programa casi toda la vista |
| **Apoyo de Controlador** | La otra persona | Responde dudas de la fachada, corrige lo que la vista descubra que falta, revisa PRs |

### 8.2 Qué recibe la vista y qué entrega (K5 en detalle)

**La vista recibe de la fachada una "foto del estado" con:**

| Dato | Para qué lo usa la vista |
|---|---|
| Sala actual (nombre, número) | Título de la sala |
| Puertas en N, S, E, O y su estado | Capa de fondo |
| Objetos del suelo y trampas (y si están armadas) | Capa estática |
| Jugador (posición, vida actual y máxima, ataque, defensa, velocidad, efectos activos) | Capa de actores y UI |
| Enemigos de la sala (tipo, comportamiento, vida actual) | Capa de actores |
| Inventario en orden, cuál está equipado | UI de inventario |
| Pergaminos disponibles | UI de deshacer |
| Últimos mensajes de bitácora | Panel de mensajes |
| Solicitudes restantes | Modo desarrollo |
| Estado de la partida (jugando, ganó, perdió, pausa) | Cambio de pantalla |
| Aviso de error amable (si hay) | Pantalla 1.6 |

**La vista entrega a la fachada solo "intenciones":** mover (N/S/E/O), atacar, equipar, soltar, recorrer inventario, deshacer, pausar, guardar, cargar, salir y elegir cripta.

### 8.3 Pasos de la Vista

Todos los elementos están descritos en la **Parte 1 del documento anterior**. Aquí se indica el orden y las dependencias.

| Paso | Qué se construye | Necesita de | Referencia del doc. anterior |
|---|---|---|---|
| **V-1** | Ventana, bucle del juego (FPS constante) y lectura de teclado traducida a intenciones | Fachada congelada | Parte 1, secciones 5 y 7 |
| **V-2** | Gestor de sprites con sprite de reemplazo | Lista de clases y comportamientos (de C2) | Parte 1, sección 6 |
| **V-3** | Pantalla de selección de cripta y pantalla de carga | Fachada: lista de criptas y estado de carga (C1 vía C2) | Parte 1, pantallas 1.2 y 1.3 |
| **V-4** | Capa de fondo: piso y puertas con 4 estados × 4 direcciones | "Foto del estado" | Parte 1, sección 2 |
| **V-5** | Capa de objetos y trampas | "Foto del estado" | Parte 1, secciones 2 y 4 |
| **V-6** | Capa de actores: jugador y enemigos con barra de vida | "Foto del estado" | Parte 1, sección 2 |
| **V-7** | UI: vida, estadísticas, inventario, mensajes | "Foto del estado" | Parte 1, sección 3 |
| **V-8** | Menú de inicio, pausa y fin de partida | Fachada: guardar, cargar, estado | Parte 1, pantallas 1.1, 1.5 y 1.7 |
| **V-9** | Pantalla de error amable y mensaje de "esperando N segundos" sin congelar la ventana | Fachada: avisos de error | Parte 1, pantalla 1.6 y regla de oro del bucle |
| **V-10** | Pulido: indicadores de efectos, modo desarrollo, revisión con el apoyo | Todo lo anterior | Parte 1, sección 3 |

**Regla de oro de la Vista:** nunca llamar directamente a C1 ni al API; nunca decidir reglas del juego. Si la vista necesita un dato que no está en la "foto del estado", **se pide por contrato (regla 6.3)** en lugar de calcularlo en la vista.

### 8.4 Qué debe esperar la Vista y de quién

| Espera | De quién | Para empezar qué paso |
|---|---|---|
| Criterio "Controlador en raya" cumplido | Ambos | V-1 en adelante |
| Fachada congelada con su lista de intenciones y foto del estado | C2 | V-1 |
| Lista final de sprites necesarios | C2 | V-2 |
| Aviso de errores y presupuesto | C1 (vía C2) | V-9 |

### 8.5 Qué entrega la Vista

| Entrega | A quién |
|---|---|
| Lista de "datos que faltan" en la foto del estado | C2, por contrato |
| Lista de "problemas de rendimiento de dibujo" | Ambos (para `--bench`) |
| Capturas de pantalla para el Documento de Decisiones de Diseño | Ambos |

---

## 9. Riesgos y preguntas abiertas

### 9.1 Preguntas ya planteadas para el profe (documento anterior)

1. ¿Las consultas de versión y los reintentos tras un 429 descuentan del presupuesto?
2. Entre `llave` en la salida y `abre` en la llave, ¿cuál manda?
3. ¿Cómo se interpretan los campos vacíos?
4. ¿Qué pasa si se agota el presupuesto?

### 9.2 Preguntas nuevas que surgieron al repartir

| # | Pregunta | Afecta a |
|---|---|---|
| 5 | ¿Cuál es la **fórmula del daño** y cómo se usa la defensa? | C2-6 |
| 6 | ¿Cómo se calcula el **tiempo entre turnos** a partir de la velocidad? | C2-3 |
| 7 | ¿Cuál es la regla de la **frescura del rastro** y cuánto dura? | C2-8 |
| 8 | ¿El **peso** de los objetos limita el inventario o solo la cantidad? | C2-5 |
| 9 | ¿Cómo se calcula el **puntaje**? | C2-10 |
| 10 | ¿Hay un **formato obligatorio** para la bitácora y el archivo binario, o es libre? | C1-8, C1-9 |
| 11 | ¿Qué debe medir exactamente `--bench`? | C1-10, Hito 3 |

> Muchas de estas respuestas pueden estar en el **enunciado original del proyecto** que no tengo. Conviene revisarlas ahí primero antes de preguntar.

### 9.3 Riesgos del plan

| Riesgo | Qué puede pasar | Cómo reducirlo |
|---|---|---|
| Que la mitad de C1 se retrase | C2 se queda sin datos reales | El proveedor falso (C1-1) lo evita |
| Que C2 cambie el estado sin avisar | El guardado de C1 se rompe | Regla de cambios 6.3 |
| Que se descubra tarde que la fachada no alcanza | La vista se detiene | La consola de pruebas usa solo la fachada desde el principio |
| Que solo uno entienda su mitad | El otro no puede revisar bien | Revisión cruzada obligatoria de PRs |
| Que la caché sea más chica que lo que una sala necesita | Se desalojan fichas recién traídas | Decidirlo en el Documento de Decisiones (Parte 4 del doc. anterior) |
| Que el presupuesto se agote antes de terminar la partida | Partida incompleta | Contador visible, lotes de 10 y precarga prudente |

---

## 10. Glosario simple

| Palabra | Qué significa aquí |
|---|---|
| **Contrato** | Acuerdo escrito entre dos partes sobre cómo se entregan datos |
| **Proveedor falso** | Versión de prueba que responde datos fijos sin internet |
| **Fachada** | La "ventanilla" que usa la Vista para hablar con todo el Controlador |
| **Foto del estado** | Un resumen de "cómo está el juego ahora mismo" para dibujarlo |
| **Intención** | Lo que el jugador quiere hacer (mover, atacar…), sin importar la tecla |
| **Instancia** | Un enemigo o trampa concreto (frente a su "molde" del catálogo) |
| **Sala lista** | Sala con esqueleto, contenido y fichas ya resueltas |
| **Determinista** | Que con las mismas acciones siempre pasa exactamente lo mismo |
| **LRU** | "Menos usado recientemente": se saca primero lo que lleva más tiempo sin usarse |
| **Hito** | Punto de revisión conjunta del equipo |
| **Consola de pruebas** | Programa de texto para jugar usando solo la fachada, antes de tener la Vista |