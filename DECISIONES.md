# DECISIONES (base del Documento de Decisiones, Hito 3)

Formato: qué / por qué / descartado.

1. **Contar toda petición (reintentos y versiones descuentan).**
   Sin respuesta del profe (pregunta 1), lo seguro es asumir el peor caso y nunca sobregirar.
   Descartado: no contar reintentos (optimista, arriesga 429 infinitos con saldo falso).

2. **`listar_criptas` fuera del contador; `info_cripta` bootstrap se descuenta al crear.**
   El total solo se conoce con la ficha, así que lo previo no puede contar; al crear se descuentan esos intentos para no regalar 2 peticiones.
   Descartado: budget 14 fijo (miente contra el API real).

3. **429 solo reintenta eso; 404/500/red propagan al primer intento.**
   El servidor dice cuánto esperar (`reintentar_en`); lo demás es bug nuestro o falla externa y reintentar quema presupuesto.
   Descartado: reintentar todo con espera fija (gasta y esconde bugs).

4. **Caché en 3 archivos (lista doble + tabla hash + LRU).**
   Hash y DLL son estructuras propias exigidas y evaluables por separado; la LRU las compone.
   Descartado: `dict` como índice o todo en un archivo (viola restricción / no reutiliza).

5. **Disco con pickle + validación por versión (Flujo H).**
   Simple y preserva las 9 clases sin parser manual; la versión evita dato rancio (1-2 peticiones baratas ahorran decenas).
   Descartado: JSON manual por clase (más código, mismo efecto) y disco sin validar (dato obsoleto).

6. **Esqueleto completo al inicio; contenido bajo demanda en lotes de 10 (N + vecinas).**
   El mapa cuesta 1 petición y se necesita para navegar/precargar; el contenido 1x1 quemaría el presupuesto (6 salas = 6 peticiones solo ahí).
   Descartado: traer todo al inicio (revienta presupuesto) y pedir de a uno (revienta presupuesto igual).

7. **`SalaLista` compartida entre falso y real.**
   C2 cambia un import y el motor sigue igual; el contrato K1 queda en tipos, no en palabras.
   Descartado: dos moldes distintos (divergen al primer cambio).

8. **Mergesort con `clave` por función, estable, sin mutar.**
   Sirve a inventario (C2-5) y puntajes (C2-10) con cualquier criterio sin reescribir; estable = determinista para `--replay`.
   Descartado: `sort`/`sorted` (prohibidos) y comparador `cmp` (más enredado que `clave`).

9. **Binario provisional con magia + versión de formato; K2 final lo cierra C2.**
   Avanza estructura y errores amables hoy sin bloquearse; la versión de formato permite migrar cuando entren agenda/pila/instancias.
   Descartado: esperar a C2 sin avanzar y formato sin versión (inmigrable).
