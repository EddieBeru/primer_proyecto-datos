# Proyecto CRIPTA: Índice de la Vista y Flujos entre Endpoints

Este documento reúne, en lenguaje sencillo, (1) todo lo que hay que programar en la **vista**, (2) lo esencial del API que entregó el profe (`openapi.json`, versión 1.0.0, solo lectura) y (3) los **flujos** que conectan los endpoints con el juego. Está basado en la guía de arquitectura del equipo y en la definición oficial del API.

---

## Parte 0: Mapa de los 8 endpoints

Todas las rutas empiezan con `/v1` y **todas exigen el carné** `X-Cripta-Client-Id`: un UUID que se genera **una sola vez al abrir el programa** y se manda en cada petición. El API lo usa solo para contar cuántas veces se pregunta.

| # | Qué hace, en simple | Ruta | Qué se le manda | Qué devuelve |
|---|---|---|---|---|
| 1 | Lista de criptas disponibles | `GET /v1/criptas` | Solo el carné | Lista con `id`, `nombre`, `salas`, `dificultad` |
| 2 | Ficha general de una cripta | `GET /v1/criptas/{id}` | Id de la cripta | Versión, total de salas, páginas, salas por página, sala inicial, sala de salida, llave de salida, presupuesto, inventario máximo, estadísticas del jugador |
| 3 | ¿Cambió esta cripta? (consulta ligera) | `GET /v1/criptas/{id}/version` | Id | Solo `id` y `version` |
| 4 | Esqueleto: una página de salas | `GET /v1/criptas/{id}/salas?pagina=N` | Id y número de página (empieza en 1) | `pagina`, `total_paginas` y hasta 50 salas con nombre y salidas |
| 5 | Contenido de hasta 10 salas | `GET /v1/criptas/{id}/contenido?salas=1,2,3` | Id y de 1 a 10 ids de sala **distintos**, separados por coma | Por sala: enemigos, objetos y trampas |
| 6 | ¿Cambió el catálogo? (consulta ligera) | `GET /v1/catalogo/version` | Solo el carné | Solo `version` |
| 7 | Varias fichas del catálogo | `GET /v1/catalogo?ids=a,b,c` | De 1 a 10 ids **distintos** | Lista `entidades` |
| 8 | Una sola ficha del catálogo | `GET /v1/catalogo/{id}` | Id | La ficha directa, sin envoltorio |

### Errores comunes a todos los endpoints

| Código | Qué significa | Cómo lo tratamos |
|---|---|---|
| 400 | Petición mal formada (por ejemplo, 11 ids o ids repetidos) | Error **nuestro**: se corrige el código, no se reintenta |
| 404 | Ese recurso no existe | Avisar al Controlador o al jugador; no reintentar |
| 429 | Demasiadas preguntas muy rápido; trae `reintentar_en` (segundos, mínimo 1) | Esperar ese tiempo y reintentar |
| 500 | El contenido publicado por el servidor es inválido | No es culpa nuestra; error amable, sin insistir sin fin |

Los errores 400, 404 y 500 traen un campo `error` con texto. El 429 trae `error` y además `reintentar_en`.

---

## Parte 1: Índice de lo que hay que programar en la vista

La vista es lo que el jugador ve y toca.

### 1. Pantallas del juego

| # | Pantalla | Qué muestra | De dónde salen los datos |
|---|---|---|---|
| 1.1 | Menú de inicio | "Jugar", "Continuar partida", "Salir" | Local. "Continuar" solo se activa si existe un archivo guardado |
| 1.2 | Selección de cripta | Tarjetas con nombre, número de salas y dificultad | Endpoint 1 |
| 1.3 | Pantalla de carga | "Preparando la cripta…" y, si hay 429, "El servidor pide esperar N segundos…" | Estado de la capa de red |
| 1.4 | Pantalla de juego | Sala actual, jugador, enemigos, objetos, trampas, puertas, mensajes, vida e inventario | Modelo + cachés |
| 1.5 | Fin de partida | Victoria o derrota, puntaje, volver al menú | Modelo |
| 1.6 | Error amable | Sin conexión, servidor ocupado, cripta no encontrada, presupuesto agotado | Errores de la capa de red |
| 1.7 | Aviso de versión cambiada | "Esta partida es de una versión anterior" y opciones | Endpoints 3 y 6 |

### 2. Las cuatro capas de dibujo

Como láminas transparentes apiladas, de abajo hacia arriba:

1. **Fondo:** piso de la sala y **puertas en las cuatro direcciones (N, S, E, O)**. Cada puerta puede verse inexistente, abierta, cerrada con llave o con cierre automático.
2. **Cosas estáticas:** `objetos` tirados en el suelo y `trampas`, armadas o desarmadas.
3. **Actores:** jugador y enemigos de la sala, cada uno con barra de vida. Conviene distinguir visualmente el `comportamiento` (guardián, errante, rastreador).
4. **Interfaz (UI):** bitácora, estadísticas e inventario.

### 3. Elementos de la interfaz y su dato exacto

| Elemento | Qué muestra | Dato del API |
|---|---|---|
| Barra de vida del jugador | Vida actual contra la máxima | `jugador.vida_max` |
| Estadísticas | Ataque, defensa, velocidad, más bonus del equipo | `jugador.*`, `ataque_bonus` del arma, `defensa_bonus` de la armadura |
| Inventario | Espacios con ícono y nombre | `inventario_max` y fichas del catálogo |
| Objeto equipado | Resaltado, siempre al frente de la lista | Regla de la guía |
| Peso y valor de cada objeto | Detalle al seleccionarlo | `peso`, `valor` |
| Indicador de llave de salida | "Tienes / no tienes la llave" | `llave_salida` |
| Estado de antorcha | Tiempo de luz restante | `duracion` |
| Efectos de pociones | "Veloz por X turnos" | `cura`, `modificador_velocidad`, `duracion` |
| Pergaminos de retroceso | Cuántos hay; tope de 5 acciones atrás | Clase `pergamino_retroceso` |
| Nombre de la sala | "Sala 3: nombre" | `Room.id`, `Room.nombre` |
| Panel de mensajes | Últimas 4 o 5 líneas de bitácora | Modelo |
| Contador de solicitudes (modo desarrollo) | Peticiones restantes | `presupuesto_solicitudes` |

### 4. Las 9 clases del catálogo y cómo dibujarlas

| Clase (`clase`) | Qué es | Datos propios | Dónde aparece |
|---|---|---|---|
| `enemigo` | Criatura hostil | `vida_max`, `ataque`, `defensa`, `velocidad`, `comportamiento`, `suelta` | Capa de actores |
| `arma` | Mejora el ataque | `ataque_bonus` | Inventario / suelo |
| `armadura` | Mejora la defensa | `defensa_bonus` | Inventario / suelo |
| `pocion` | Cura y/o cambia la velocidad por un tiempo | `cura`, `modificador_velocidad`, `duracion` (cualquiera puede venir vacío) | Inventario / suelo |
| `antidoto` | Quita el veneno | Solo lo básico | Inventario / suelo |
| `llave` | Abre una puerta | `abre` (id de sala, texto o vacío) | Inventario / suelo |
| `antorcha` | Da luz un tiempo | `duracion` | Inventario / suelo |
| `pergamino_retroceso` | Deshace acciones | Solo lo básico | Inventario / suelo |
| `trampa` | Hace daño al pisarla | `daño`, `rearme` (puede venir vacío); opcionales `veneno` y `quemadura`/`fuego` (daño por pulso, ver anexo de la guía) | Capa estática |

Todos los objetos (menos la trampa) comparten `id`, `nombre`, `peso` y `valor`. La trampa no tiene peso ni valor porque no se carga.

**Recomendación:** un solo "dibujante de entidades" que, según la clase, elija el ícono. Así agregar una clase nueva se hace en un único lugar.

### 5. Entrada del jugador (teclado)

La vista solo traduce teclas en intenciones y se las pasa al Controlador.

| Tecla sugerida | Intención | Nota |
|---|---|---|
| W / ↑ | Moverse al Norte | Direcciones del API: N, S, E, O |
| S / ↓ | Moverse al Sur | |
| D / → | Moverse al Este | |
| A / ← | Moverse al Oeste | "O" de Oeste |
| Espacio | Atacar | |
| E | Equipar | Mueve el objeto al frente del inventario |
| Q | Soltar | De cualquier posición |
| Tab | Recorrer inventario | Lista doble: adelante y atrás |
| U | Usar pergamino de retroceso | Deshace hasta 5 acciones |
| Esc | Pausa | Con opción de guardar |

### 6. Gestor de recursos gráficos

- Cargar todos los sprites **una sola vez** al iniciar.
- Agrupar por: piso, puertas (4 estados × 4 direcciones), jugador, enemigos (3 comportamientos), 9 clases de objetos, trampas, íconos de UI.
- Tener un **sprite de reemplazo** (cuadro de color) para ids sin imagen. El catálogo lo define el profe y pueden aparecer entidades no previstas.

### 7. Bucle del juego (game loop)

1. Leer teclas.
2. Pasarlas al Controlador.
3. Avanzar el reloj virtual del Modelo.
4. Dibujar las cuatro capas.
5. Esperar lo justo para mantener los FPS.

**Regla de oro:** las peticiones de red nunca deben congelar este bucle. Si hay un 429 con `reintentar_en: 5`, la ventana sigue viva mostrando "esperando…".

### 8. Lo que la vista NO hace

- No habla con el API.
- No calcula daño, no mueve enemigos, no decide victorias.
- No guarda archivos.

Solo muestra y avisa lo que el jugador quiere hacer.

---

## Parte 2: Conceptos clave del API

### A. Dos mitades de cada sala: esqueleto y contenido

| Mitad | Qué contiene | Cómo se pide | Tamaño del lote |
|---|---|---|---|
| **Esqueleto** | `id`, `nombre`, `salidas` (el mapa) y, si la sala está a oscuras, `oscura`/`oscuridad` | Por **páginas** (endpoint 4) | Hasta 50 salas por página |
| **Contenido** | `enemigos`, `objetos`, `trampas` (y puede declarar también `oscura`/`oscuridad`) | Por **lista de ids** (endpoint 5) | De 1 a 10 salas por petición |

El esqueleto es el **plano** del edificio; el contenido es **lo que hay dentro de cada cuarto**.

### B. Las salidas

Cada sala puede tener hasta 4 salidas: **N, S, E, O**. Cada una dice:

| Campo | Significado | ¿Siempre viene? |
|---|---|---|
| `sala` | A qué sala lleva | Sí |
| `cerrada` | Si empieza cerrada | No |
| `llave` | Qué llave la abre | No |
| `cierre_automatico` | Se vuelve a cerrar sola tras ese tiempo | No |

Dos detalles importantes:

- Las salidas son **dirigidas**: poder ir de la sala 1 a la 2 no garantiza poder volver. Hay que respetar lo que diga cada sala.
- El API describe el **estado inicial**, no el estado vivo. Si una puerta se abre o cierra durante la partida, eso lo lleva el **Modelo**.

### C. Instancia contra tipo

En el contenido de una sala, cada enemigo o trampa trae:

| Campo | Significado |
|---|---|
| `tipo` | A qué entrada del catálogo corresponde |
| `instancia` | Identificador de **este** enemigo o trampa en particular |
| `vida` (solo enemigos) | Vida con la que empieza; puede venir vacía |

El catálogo es el **molde** y la instancia es **cada galleta** hecha con ese molde. El estado cambiante (vida, trampa armada o no) se guarda **por instancia**, no por tipo. Si una sala tiene dos esqueletos y mataste a uno, el otro sigue vivo.

Los `objetos` de una sala son una lista simple de ids de catálogo, sin instancia.

### D. Lo que suelta un enemigo

El enemigo tiene `suelta`: lista de ids de catálogo (puede ser vacía o nula). Al morir, esos objetos aparecen en el suelo. Para dibujarlos, sus fichas deben estar en caché.

### E. El presupuesto de solicitudes

La ficha general trae `presupuesto_solicitudes` (9 en el ejemplo, para 6 salas). Hace falta un **contador propio**.

Ejemplo con la cripta de 6 salas: lista (1) + ficha (1) + esqueleto, que cabe en 1 página (1) + contenido por lote de 10 (1) = **4 de 9**, quedan 5 para el catálogo. Por eso los lotes importan.

Mientras el profe no confirme qué cuenta, la postura segura es **contar todas las peticiones**, incluidas las consultas de versión y los reintentos tras un 429.

### F. Versiones

| Versión | De qué es | Endpoint ligero | Para qué |
|---|---|---|---|
| `version` de la cripta | Esqueleto + contenido de esa cripta | `/v1/criptas/{id}/version` | Validar partidas guardadas y cachés de salas |
| `version` del catálogo | El catálogo global | `/v1/catalogo/version` | Validar la caché de entidades |

Son **independientes**. La caché guardada en disco debe anotar ambas.

---

## Parte 3: Flujos entre endpoints

### Flujo A: Arranque

```
Abrir programa
   │
   ▼
Crear carné (UUID) una sola vez ──► guardarlo para toda la sesión
   │
   ▼
Pedir lista de criptas  [endpoint 1]
   │
   ├─ 200 ──► pantalla de selección
   ├─ 429 ──► esperar `reintentar_en` segundos y reintentar (Flujo F)
   ├─ 500 ──► error amable: "el servidor tiene un problema"
   └─ Sin red ──► error amable + "reintentar" o "usar lo guardado"
```

Este paso cumple la verificación de conexión que pide la guía sin gastar una petición extra.

### Flujo B: Elegir cripta y preparar la partida

```
Jugador elige una cripta
   │
   ▼
Pedir ficha general  [endpoint 2]
   │   Recibimos: versión, salas_total, paginas, salas_por_pagina,
   │   sala_inicial, sala_salida, llave_salida,
   │   presupuesto, inventario_max, jugador
   ▼
Crear el contador de presupuesto con el valor recibido
   │
   ▼
Pedir esqueleto: página 1  [endpoint 4]
   │
   ├─ ¿total_paginas > 1? ──► pedir las páginas restantes
   ▼
Pedir contenido de la sala inicial  [endpoint 5]
   │
   ▼
Con los ids de enemigos, objetos y trampas de esa sala:
   Pedir fichas al catálogo  [endpoint 7, hasta 10 ids por petición]
   │
   ▼
El Modelo construye el estado inicial:
   • Jugador con las estadísticas de la ficha general
   • Inventario vacío con tope inventario_max
   • Sala actual = sala_inicial
   • Meta = estar en sala_salida con llave_salida
   │
   ▼
Entrar a la pantalla de juego
```

**Nota:** el esqueleto pesa poco y es el plano para navegar, así que conviene pedirlo completo al inicio y guardarlo. El contenido y el catálogo se piden bajo demanda.

### Flujo C: Entrar a una sala nueva (el corazón del juego)

```
El jugador cruza una puerta hacia la sala N
   │
   ▼
¿Tenemos el CONTENIDO de la sala N guardado?
   │
   ├─ SÍ ──► usarlo
   │
   └─ NO ──► ¿Hay presupuesto?
              │
              ├─ NO ──► el Controlador decide (ver Parte 4)
              │
              └─ SÍ ──► Pedir contenido de hasta 10 salas juntas  [endpoint 5]
                         (la N más vecinas probables)
                         Restar 1 al presupuesto
   │
   ▼
Con el contenido en mano, listar los ids necesarios:
   tipos de enemigos + tipos de trampas + objetos + lo que sueltan los enemigos
   │
   ▼
Para cada id: ¿está en la caché LRU del catálogo?
   │
   ├─ Todos están ──► 0 peticiones
   │
   └─ Faltan algunos ──► agruparlos en lotes de máximo 10
                         Pedir cada lote  [endpoint 7]
                         Restar 1 por lote al presupuesto
                         Guardar fichas nuevas en la caché
                         ¿Se pasó --cache-size? → sacar la menos usada
   │
   ▼
Armar la sala viva para el Modelo y dibujarla
```

**Cómo ahorrar peticiones, de mayor a menor impacto:**

1. **Agrupar contenido:** 10 salas por petición, no una por una.
2. **Agrupar catálogo:** reunir todos los ids que faltan **antes** de preguntar y pedirlos en lotes de 10. Nunca usar el endpoint 8 en un bucle.
3. **Evitar ids repetidos:** el API exige ids distintos; si dos enemigos son del mismo tipo, el id va una sola vez. Repetirlo da 400.
4. **Aprovechar la caché:** las fichas se reutilizan en todas las salas y hasta entre partidas.
5. **Precargar:** con el esqueleto se sabe qué salas son vecinas; pedir su contenido junto con el de la actual en la misma petición de 10.

El endpoint 8 (ficha única) sirve para casos sueltos, como un objeto inesperado que no se había previsto.

### Flujo D: Partida completa

```
Flujo B (preparación)
   │
   ▼
┌───────────────── BUCLE DE JUEGO ─────────────────┐
│ 1. Tecla → Vista → Controlador                   │
│ 2. Controlador le pide la acción al Modelo       │
│ 3. Modelo guarda la acción inversa en la pila    │
│    (máx. 5, para el pergamino de retroceso)      │
│ 4. Modelo programa eventos en la agenda:         │
│    veneno, trampas, cierre automático de puertas,│
│    turnos de enemigos, fin de pociones/antorcha  │
│ 5. La agenda saca el evento más próximo          │
│    (cola de prioridad; desempate por secuencia)  │
│ 6. ¿Cruzó una puerta? → Flujo C                  │
│ 7. La bitácora anota lo ocurrido                 │
│ 8. La vista se redibuja                          │
└──────────────────────────────────────────────────┘
   │
   ▼
¿En sala_salida con la llave_salida? ──► Victoria
¿Vida en 0? ──► Derrota
   │
   ▼
Puntaje → Pantalla de fin
```

**Cómo se conecta con los datos del API:**

- **Velocidad** (jugador y enemigos): decide cada cuánto tiempo virtual les toca actuar. Es la materia prima de la agenda.
- **Cierre automático:** si una salida trae `cierre_automatico`, al abrirla se programa en la agenda "esta puerta se cierra en X".
- **Rearme de trampas:** si trae `rearme`, tras dispararse se programa "volver a armarse".
- **Pociones y antorchas:** cada una programa un evento de fin de efecto.
- **Comportamientos de enemigos:**
  - `guardián`: se queda cuidando su sala.
  - `errante`: se mueve entre salas.
  - `rastreador`: sigue el rastro fresco del jugador.

### Flujo E: Puertas y llaves

```
El jugador intenta pasar por una salida (N/S/E/O)
   │
   ▼
¿Esa salida existe en la sala?
   ├─ NO ──► "No hay camino por ahí"
   └─ SÍ ──► ¿Está cerrada (estado vivo del Modelo)?
              ├─ NO ──► pasar a la sala destino (Flujo C)
              └─ SÍ ──► ¿La salida pide llave?
                         ├─ NO pide ──► "Está trabada" (según reglas del juego)
                         └─ SÍ pide ──► ¿El inventario tiene esa llave?
                                         ├─ SÍ ──► abrir; si trae cierre_automatico,
                                         │         programar el cierre en la agenda
                                         └─ NO ──► "Necesitas la llave X"
```

**A aclarar con el profe:** la ficha de la llave trae `abre` (id de sala, texto o vacío) y la salida trae `llave` (id de llave). Hay dos formas de relacionarlas; conviene confirmar cuál manda si aparecen las dos.

### Flujo F: Manejo del 429

```
Petición enviada
   │
   ▼
¿Respondió 429?
   ├─ NO ──► continuar
   └─ SÍ ──► leer `reintentar_en` (segundos, mínimo 1)
              │
              ▼
           Mostrar "esperando N segundos…" (sin congelar la ventana)
              │
              ▼
           Reintentar la MISMA petición
              ├─ OK ──► continuar
              └─ 429 otra vez ──► repetir, con número máximo de intentos
                                  │
                                  └─ Se acabaron ──► error amable
```

El servidor dice exactamente cuánto esperar, así que no hay que inventar tiempos. Aun así, definan un tope de intentos y un **timeout** explícito en cada petición.

### Flujo G: Guardar y cargar partida

```
GUARDAR                                  CARGAR
Modelo entrega su estado                 Leer archivo binario
   │                                        │
   ▼                                        ▼
Convertir a bytes (struct)               Validar formato
   │                                        │
   ▼                                        ▼
Escribir archivo                         Reconstruir el Modelo
(con id de cripta, versión de la            │
cripta y versión del catálogo)              ▼
                                         Consultar [endpoint 3] y [endpoint 6]
                                            │
                                            ├─ Ambas versiones iguales ──► continuar
                                            └─ Alguna cambió ──► aviso (pantalla 1.7)
```

**Qué debe llevar el archivo:** id y versión de la cripta, versión del catálogo, sala actual, jugador (vida, posición, efectos activos), inventario en orden, equipo, estado vivo de **cada instancia** (enemigos y trampas), estado vivo de las puertas, salas visitadas, agenda de eventos pendientes, reloj virtual, presupuesto restante y pila de deshacer.

**Por qué dos consultas de versión:** son las más baratas del API. Gastar 2 peticiones al cargar protege de jugar con datos desactualizados.

### Flujo H: Caché en disco y su validación

```
Al arrancar, si existe caché local:
   │
   ▼
Pedir versión del catálogo  [endpoint 6]
   ├─ Igual a la guardada ──► la caché del catálogo sirve
   └─ Distinta ──► invalidar la caché del catálogo

Al elegir una cripta con datos guardados:
   │
   ▼
Pedir versión de la cripta  [endpoint 3]
   ├─ Igual ──► esqueleto y contenido guardados sirven (ahorran peticiones)
   └─ Distinta ──► descartar y volver a pedir
```

### Flujo I: Bitácora y repetición (`--replay`)

```
Cada acción relevante ──► una línea de texto al final del archivo (solo agregar)

Modo --replay:
   Leer línea por línea ──► reproducir ──► llegar al mismo resultado
```

Requiere que el juego sea **determinista**. Por eso la agenda desempata por número de secuencia, y por eso los ids de **instancia** son útiles: identifican sin ambigüedad a cada enemigo y trampa en el registro.

---

## Parte 4: Casos difíciles para decidir en equipo

| Situación | Pregunta a resolver |
|---|---|
| Se agota el presupuesto a mitad de partida | ¿Se juega solo con lo ya cargado, se corta la partida o se calcula de antemano si alcanza? |
| Un 429 consume presupuesto | Confirmar con el profe; mientras tanto, contarlo |
| Las consultas de versión consumen presupuesto | Confirmar con el profe |
| `--cache-size` es menor a lo que necesita una sala | ¿Se fija un mínimo, o se permite volver a pedir fichas? |
| Una sala trae más de 10 ids de catálogo distintos | Dividir en lotes de 10 y contar cada uno |
| Un id se repite en una petición | Evitarlo siempre; el API espera ids distintos |
| Una ficha de catálogo no existe (404) | ¿Sprite genérico, omitir el objeto o abortar? |
| `suelta` de un enemigo apunta a un id nunca visto | Precargar las fichas de `suelta` al cargar la sala |
| La versión de la cripta cambió respecto a lo guardado | ¿Se invalida el guardado o se intenta cargar igual? |
| Campos opcionales vacíos (`cerrada`, `cura`, `rearme`, `vida`, etc.) | Definir un valor por defecto en el Modelo para cada uno |
| La llave trae `abre` y la salida trae `llave` | Confirmar cuál regla manda |
| Varios eventos en el mismo instante virtual | El número de secuencia desempata; probar con casos reales |
| Sin internet pero con caché local | ¿Se permite jugar solo hasta donde llegue lo guardado? |

---

## Parte 5: Reparto de la vista

- **Integrante 1 (UI y assets):** gestor de sprites, menú de inicio, pantalla de fin, inventario gráfico y el "dibujante de entidades" de las 9 clases (secciones 1.1, 1.5, 3, 4 y 6 de la Parte 1).
- **Integrante 2 (bucle y sincronización):** game loop, rejilla de la sala, dibujo de puertas N/S/E/O y teclado hacia el Controlador (secciones 1.4, 2, 5 y 7).
- **En conjunto:** selección de cripta, carga y errores, que dependen del cliente de red (Bloque 1).

---

## Preguntas para el profe (el API no las responde)

1. ¿Las consultas de versión (endpoints 3 y 6) y los reintentos tras un 429 descuentan del `presupuesto_solicitudes`?
2. Cuando una salida tiene `llave` y la ficha de la llave tiene `abre`, ¿cuál es la regla definitiva?
3. ¿Cómo se interpretan los campos que pueden venir vacíos (`cerrada`, `rearme`, `cura`, `vida` de la instancia)? ¿"Vacío" significa "no aplica" o "valor por defecto"?
4. ¿Qué pasa si se agota el presupuesto: se pierde la partida o simplemente no se pueden pedir más datos?