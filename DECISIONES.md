# DECISIONES (Documento de Decisiones de Diseño, §8)

Dos partes: (A) el documento por problema de §4 con problema, alternativas,
decisión, complejidad, evidencia `--bench` y límites; (B) la bitácora
numerada de decisiones (formato qué / por qué / descartado) que el grupo
fue acumulando y que alimenta la parte A.

Mediciones de la parte A: `python -m src.main --bench` (máquina del grupo,
mejor de 3 repeticiones; el cronómetro varía ~±50% entre corridas, las
comparaciones se hacen dentro de la misma corrida).

## A. Documento por problema (§4.1–§4.11)

### §4.1 Qué ocurre a continuación (agenda de eventos)

- **Problema.** Cada paso del bucle saca el evento pendiente con menor
  `(t, seq)` sin examinar todos los eventos; los actores mueren (sus
  eventos se cancelan), los efectos se cancelan antes de activarse y el
  orden debe quedar determinista. Operaciones reales por turno jugado:
  1 `ver_proximo`+`sacar_proximo` por evento drenado (decenas), varias
  `programar` por activación de sala (turnos, regeneración, veneno,
  oleadas) y `cancelar_por_seq` al deshacer. Con 500 eventos en vuelo y
  decenas de miles de extracciones (§4.1).
- **Alternativas.** (a) Lista simplemente enlazada ordenada (la versión
  anterior): sacar es O(1) pero cancelar por seq exige barrer; el antídoto
  usaba `cancelar_donde` (barrido completo). (b) Montículo binario propio:
  O(log n) sacar/insertar, pero cancelar un evento arbitrario (muerte,
  efecto, deshacer) requiere búsqueda o borrado perezoso, y el desempate
  estable por `seq` complica. Descartada (a) por el barrido del antídoto;
  descartada (b) por el costo de las cancelaciones, que en este juego son
  tan frecuentes como las extracciones.
- **Decisión.** Agenda como lista doble ordenada por `(t, seq)` (cabeza y
  cola), con caminos O(1): sacar el próximo, desenlazar un nodo conocido y
  reinsertar al final cuando el reloj avanza. Índices internos propios
  (sin `dict`, §7): hash encadenado `tipo → lista intrusiva de nodos` y
  lista `seq → nodo` compactable. `cancelar_tipo(tipo)` recorre solo los
  eventos de ese tipo; `cancelar_por_seq(seq)` es O(1).
- **Complejidad.** `ver_proximo`/`sacar_proximo` O(1); `programar` O(1)
  amortizado en el patrón real (t creciente) y O(n) en el peor caso
  (inserciones con t viejo); `cancelar_por_seq` O(1); `cancelar_tipo` O(k);
  `cancelar_donde` O(n) (queda solo para predicados sueltos, p. ej.
  `datos["actor"]` en deshacer de enemigos).
- **Evidencia (`--bench`).** `agenda_500` (500 altas desordenadas + vaciado)
  = 0.011 s. `agenda_cancelar_tipo_20k` = 0.0009 s vs
  `agenda_cancelar_barrido_20k` = 0.0025 s (misma agenda de 20 000 eventos,
  400 de tipo veneno): el índice es ~3× más rápido y además la única
  operación del antídoto; el barrido queda en el bench como la alternativa
  descartada medida. `retroceso_200` (200 apilar+desapilar con cancelación
  por seq O(1)) = 0.0002 s.
- **Límites.** Si la mayoría de las inserciones vinieran con `t` en el
  pasado (no es el patrón del reloj), `programar` degeneraría en O(n) por
  alta; con varios cientos de miles de eventos en vuelo convendría el
  montículo con borrado perezoso.

### §4.2 Traer el contenido antes de que haga falta

- **Problema.** Entrar a una sala exige su contenido ya disponible; pedirlo
  al cruzar la puerta costaría ~400 ms de espera. Operaciones reales: al
  armar cada sala se piden lotes de hasta 10 salas (contenido) y lotes de
  catálogo; al empezar, 1 esqueleto completo.
- **Alternativas.** (a) Pedir 1×1 al cruzar cada puerta: 6 salas = 6
  solicitudes tardías y el jugador espera; (b) traer todo el contenido al
  inicio: quema el presupuesto con mapas grandes. Descartadas ambas.
- **Decisión.** Esqueleto completo al inicio (1 solicitud) + contenido en
  lotes de 10 al armar la sala y sus vecinas del plano (§2.4: las vecinas
  entran dormidas). Las solicitudes se hacen antes de confirmar el
  movimiento; si algo falta,`_asegurar_fichas` lo trae como respaldo.
- **Complejidad.** Cada contenido se pide una vez por versión vigente
  (O(1) amortizado por sala); armar vecinas es O(grado) sobre el plano.
- **Evidencia.** `ciclo_completo_s` = 0.004 s: iniciar + 12 pasos hasta
  victoria (esqueleto, sala inicial con vecinas dormidas, combate, trampas,
  apertura de puertas) con caché y almacén en disco reales y red sintética.
- **Límites.** El lote de 10 deja de alcanzar si una cripta tuviera pasillos
  de >9 vecinas simultáneas; el costo de red del servidor real (400 ms) no
  está en el bench (offline), se contabiliza en presupuesto, no en reloj
  virtual.

### §4.3 Resolución de referencias del catálogo

- **Problema.** Los ids se descubren en orden no controlado, se repiten
  entre salas y criptas; resolverlos 1×1 no cabe en el presupuesto.
  Operación frecuente: averiguar si una ficha ya está en memoria antes de
  pedirla (una vez por entidad al armar cada sala).
- **Alternativas.** (a) `dict` como índice — prohibido por §7;
  (b) solicitar cada id al descubrirlo — quema el presupuesto.
- **Decisión.** `lote_catalogo_auto(ids)` agrupa ids nuevos en una
  solicitud; la caché LRU (tabla hash propia + lista doble) y el almacén en
  disco resuelven el resto en memoria/disco. El proveedor acumula
  `catalogo` para que C2 nunca vea ids sin ficha.
- **Complejidad.** Consulta de caché O(1); lote O(ids nuevos).
- **Evidencia.** `cache_hits_2000` = 0.0029 s (≈1.5 µs por acierto);
  `almacen_recupera_200` = 0.0018 s (≈9 µs por ficha desalojada leída de
  disco), contra ~400 ms de una solicitud de red.
- **Límites.** La tabla hash es de la LRU; si el catálogo de una cripta
  cabalgara sobre decenas de miles de fichas el factor de carga de las
  cubetas debería re-dimensionarse (hoy fijo).

### §4.4 Reutilización y caché persistente

- **Problema.** Tope configurable de fichas en memoria (`--cache-size`,
  default 25); al desalojar, la ficha queda en disco; recuperarla cuesta
  una lectura de disco, no red; las fichas en uso (enemigo vivo, inventario,
  suelo/trampas de la sala actual) jamás se desalojan; la caché sobrevive
  al cierre y se valida por versión.
- **Alternativas.** (a) LRU puro sin pin: desalojaba fichas en uso y el
  juego pedía red para objetos visibles; (b) pin de todo el catálogo
  (versión anterior): con 25 de tope nada podía desalojarse. Descartadas.
- **Decisión.** `CacheLRU` (tabla hash + lista doble) con `fijar_en_uso`
  recalculado desde el estado real; `AlmacenFichas` (archivo append-only
  con índice hash id→offset) persiste cada ficha al salir de la LRU. La
  sesión fija solo lo que la partida usa: vivos, suelo, trampas e
  inventario de la sala actual. Al recuperar del almacén, la ficha vuelve
  a la LRU.
- **Complejidad.** Consulta O(1), desalojo O(1), recuperación de disco
  O(1) + deserialización de 1 ficha; fijar en uso O(fichas en uso).
- **Evidencia.** `cache_hits_2000` 0.0029 s / `cache_misses_2000` 0.0036 s
  (las consultas fallidas también son O(1)); `cache_disco_guarda` 24 µs y
  `cache_disco_carga` 94 µs para 25 fichas; `almacen_recupera_200` 9 µs por
  ficha. Prueba `test_ficha_desalojada_se_recupera_sin_red` (LRU de 2 con
  backend que cuenta lotes: recuperar no pide red).
- **Límites.** El almacén hace append y no compacta: con muchísimas
  versiones del catálogo el archivo crece (hoy se trunca al cambiar de
  versión). El pin asume que la sala actual es la única visible; vistas que
  muestren dos salas a la vez requerirían ampliarlo.

### §4.5 Inventario

- **Problema.** Recorrer hacia adelante y atrás, soltar en cualquier
  posición sin costo según posición, equipar mueve al frente, vista
  ordenada por peso/valor/nombre sin tocar el orden real, tope de capacidad.
- **Alternativas.** (a) Lista doble + iterador (la anterior, correcta) sin
  exponer la vista ordenada en la interfaz ni en la consola; (b) array con
  índices. Descartada (b) por el costo de soltar en el medio.
- **Decisión.** `ListaDoble` con cursor para el recorrido; soltar desenlaza
  el nodo actual O(1); equipar mueve al frente O(1); la vista ordenada la
  produce el mergesort de C1 inyectado (`orden_fn`) sobre una copia. La
  consola expone `inventario [nombre|peso|valor]` y la vista cicla criterios
  (C) y marca "E" las equipadas.
- **Complejidad.** Recorrer O(1) por paso; soltar/equipar O(1); vista
  ordenada O(n log n) sobre copia (n ≤ inventario_max).
- **Evidencia.** `inventario_recorre` = 12 µs (100 objetos, ida y vuelta);
  `inventario_suelta_equipar` = 4 µs (soltar en el medio + recoger +
  equipar).
- **Límites.** La vista ordenada depende de `peso`/`valor` presentes en la
  ficha; fichas sin esos campos ordenan al final (documentado en `orden`).

### §4.6 Pergaminos de retroceso e historial reversible

- **Problema.** Volver al estado anterior a la última acción incluyendo los
  eventos ejecutados después; prohibido guardar copias completas; tope 5
  acciones; el pergamino queda consumido y excluido del estado reversible.
- **Alternativas.** (a) Snapshot completo del estado por acción (prohibido
  y O(estado) por acción); (b) reversión por inversas (implementada).
- **Decisión.** Cada acción del jugador apila una inversa mínima
  (`{"op", "datos", "eventos"}`) en `PilaDeshacer` (lista doble, tope 5,
  descarta lo más antiguo); deshacer aplica la inversa, cancela los eventos
  agendados por seq O(1) y restaura reloj/rastro/vida/inventario/puertas/
  trampas. El pergamino usado se descuenta aparte del historial.
- **Complejidad.** Apilar O(1); deshacer O(eventos de la acción) por las
  cancelaciones O(1) (antes O(agenda) cada una). No hay copias completas.
- **Evidencia.** `retroceso_200` = 0.0002 s (200 apilar+desapilar).
  Pruebas de inversas por operación en `test_controlador.py`
  (regeneración, oleadas, trampas, equipo, torretas).
- **Límites.** La garantía es "una acción atrás por deshacer" (§2.11); si
  dos acciones se entrelazaran con drenajes parciales el historial asume
  que el drenaje completo ocurre entre acciones (así lo hace la Sesión).

### §4.7 El rastro del jugador

- **Problema.** La decisión de un rastreador cuesta proporcional a las
  salidas de su sala (no al tamaño de la cripta ni al recorrido); rastro
  caduca a 400; trabajo total por ciclo lineal en los enemigos que actúan.
- **Alternativas.** (a) Caducar activamente (recorrer la cripta limpiando
  marcas viejas): paga O(cripta) aunque nadie rastree; (b) detectar la
  caducidad al consultar (implementada): cero trabajo si no hay
  rastreadores actuando.
- **Decisión.** `sala.ultima_visita` (timestamp por sala) + umbral 400 al
  consultar; el rastreador compara sus salidas abiertas y elige la más
  fresca (empate menor id). Errantes usan azar reproducible; guardianes
  esperan.
- **Complejidad.** O(salidas de la sala) por decisión de rastreador; total
  por ciclo lineal en rastreadores activos.
- **Evidencia.** Cubierto por el ciclo completo (`ciclo_completo_s`, las
  sombras rastreadoras del mapa fake cruzan entre salas) y las pruebas de
  determinismo del errante/rastreador; sin bench aislado.
- **Límite conocido.** La localización del enemigo dentro de `decidir_destino`
  hoy barre las salas del estado (`_sala_de`): con mapas muy grandes y
  muchos rastreadores ese barrido domina. Mejora pendiente: registrar la
  ubicación de cada instancia al moverla.

### §4.8 Bitácora en pantalla

- **Problema.** Mostrar solo los últimos 20 mensajes con memoria constante,
  sin desplazar físicamente los 19 anteriores al agregar.
- **Alternativas.** (a) Lista con `pop(0)`/corte `[-20:]`: copia o
  desplazamiento por mensaje; (b) deque con tope: no propia y opaca;
  (c) buffer circular propio (implementado).
- **Decisión.** `BufferCircular(20)` en la fachada: arreglo fijo de 20
  posiciones con índice de escritura módulo 20; `ultimos(k)` reconstruye
  los últimos k en orden. La consola imprime los 20; (la vista mantiene su
  decisión 49: toast + resaltes, sin panel de bitácora).
- **Complejidad.** Agregar O(1) sin desplazamientos; memoria O(1) (20
  posiciones fijas sin importar la partida).
- **Evidencia.** `buffer_100k_agrega` = 0.027 s por 100 000 mensajes
  (≈0.3 µs por mensaje); `buffer_largo` = 20 tras 100 000 altas.
- **Límites.** El tope 20 es fijo por §10.2; si se quisiera una ventana
  histórica mayor habría que parametrizar el buffer.

### §4.9 Ordenamiento

- **Problema.** Ordenar puntajes, vistas de inventario, índice del guardado
  y listas auxiliares (vecinas, agenda reconstruida). Prohibido `sorted`/
  `list.sort` para los ordenamientos evaluados. Tamaños reales: inventario
  ≤ 10-100, índices de guardado ≤ salas, puntajes de la tabla local (decenas
  a miles), datos casi ordenados en reconstrucción de agenda.
- **Alternativas.** (a) Solo mergesort: correcto pero paga O(n log n) aun
  con datos casi ordenados; (b) solo inserción: O(n²) en datos mezclados.
  Descartadas individualmente.
- **Decisión.** Dos algoritmos propios con `clave` (estables, sin mutar):
  mergesort estable para tamaños grandes/mezclados e inserción para n ≤ 32
  o casi ordenado; `orden_auto` elige por propiedades medibles (n y
  desorden). C2 no importa C1: usa su inserción local (`orden_local`) para
  la agenda reconstruida y el padrón de salas; la Sesión inyecta
  `vista_ordenada` (mergesort de C1) en la fachada.
- **Complejidad.** O(n log n) mezclado; O(n) casi ordenado con inserción.
- **Evidencia.** `insertsort_casi_2000` = 0.00036 s vs
  `mergesort_casi_2000` = 0.0035 s (10× a favor de inserción en
  casi-ordenado); `orden_auto_500` 0.0016 s vs `mergesort_500` 0.0017 s
  (empate a tamaño chico); `orden_auto_8000` 0.023 s vs `mergesort_8000`
  0.020 s. Las alternativas descartadas quedan medidas en el propio bench.
- **Límites.** El umbral 32/razón de desorden está fijado por mediciones
  locales; con claves de comparación muy costosas el punto de corte se
  correría hacia la inserción.

### §4.10 Guardado binario de la partida

- **Problema.** Formato binario propio, cargar una sala sin leer todo el
  archivo, detectar incompatibilidad de versión y comparar contra JSON.
- **Alternativas.** (a) JSON manual por clase (volumen y sin salto
  aleatorio); (b) pickle completo del estado (sin índice, sin formato
  propio).
- **Decisión.** v2 con magia + versión de formato + índice de salas
  (offset/largo por sala, ordenado con mergesort); cargar una sala lee solo
  su blob; v1 solo lectura. `comparar_json` mide tamaño y tiempo contra el
  JSON equivalente.
- **Complejidad.** Guardar O(salas); cargar 1 sala O(1) búsqueda en índice
  + O(blob); cargar todo O(archivo).
- **Evidencia.** `guardado_bin_bytes` 600 vs `guardado_json_bytes` 595;
  carga completa `guardado_bin_carga_s` 44 µs vs `guardado_json_carga_s`
  11 µs. Honesto: en un estado tan chico el JSON es más rápido de cargar
  entero; la ventaja del binario es el acceso por sala (una sala de un
  archivo grande sin parsear el resto) y la validación de formato.
- **Límites.** Con el estado actual el binario no gana en tamaño; ganaría
  con muchas instancias repetidas (pickle comparte referencias) o si se
  midiera carga de una sala en archivos de cientos de salas.

### §4.11 Bitácora de partida y reproducción

- **Problema.** Registrar cada acción en un archivo de solo anexado con
  header (cripta, versiones, semilla); `--replay` reproduce sin
  interacción; si la versión no está disponible, avisar y no reproducir
  contra datos distintos.
- **Alternativas.** (a) Sin header: imposible validar; (b) reproducir
  silenciosamente contra la versión actual: resultados falsos.
- **Decisión.** K3: header `#cripta <id> <ver> <vercat> <semilla>` +
  líneas `t|accion|...` de solo append; el replay valida header contra el
  backend (o el paquete offline) y reconstruye con la misma semilla; si la
  versión no está disponible, error amable.
- **Complejidad.** Escribir O(1) por acción; reproducir O(líneas) + el
  costo normal del motor.
- **Evidencia.** `ciclo_completo_s` juega con `log_ruta` desactivado para
  medir el motor; `--replay partida.log` sobre la bitácora real del repo
  funciona offline (`paquete_demo/`); pruebas de header inválido/versión
  distinta en `test_sesion.py`.
- **Límites.** La reproducción fiel depende de que el backend o el paquete
  offline conserven las versiones listadas; si no, solo avisa.

## B. Bitácora de decisiones (qué / por qué / descartado)

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

10. **Daño con randint(0,4) y Random(semilla).** Doc §2.6 lo exige + reproducibilidad. Descartado: determinista sin azar (no coincide observable).
11. **Intervalo por costo (`costo*100//vel`) + reescale.** Doc §2.3 + tabla costos. Descartado: `base//vel` único (mover≠recoger).
12. **Rastro timestamp + fresco <400, empate menor id.** Doc §2.9/§4.7. Descartado: intensidad con decaimiento (otra semántica).
13. **Errante con azar, rastreador solo vecinas abiertas.** Doc §2.8. Descartado: hash determinista sin RNG.
14. **Abrir(50)≠mover(100), llave no consume.** Doc §2.5. Descartado: auto-abrir al mover.
15. **Veneno 80x5=400, rearme 300 default, regen 200 capada.** Doc §2.10. Descartado: ticks genéricos.
16. **Victoria con puerta abierta, tabla sin fórmula.** Doc §2.12. Descartado: puntaje `salas*100...` y victoria con llave en bolsillo.
17. **Pergamino por intervalo + exclusión + tope 5, sin copias.** Doc §2.11/§4.6. Descartado: una entrada por evento (revierte de a uno).
18. **Bitácora header + validación, pantalla 20 circular.** Doc §4.11/§4.8. Descartado: sin header y `mensajes[-50:]`. (Nota: el "circular" real llegó en la decisión 56; hasta entonces la fachada recortaba una lista.)
19. **Presupuesto cuenta todo incl lista; offline no cuenta.** Doc §5.1. Descartado: lista gratis.
20. **Caché 25 + pin en-uso + disco.** Doc §4.4. Descartado: LRU puro sin pin.
21. **Guardado v2 con índice por sala + comparativa JSON.** Doc §4.10. Descartado: secuencial completo.
22. **Dos sorts + auto (n<=32 o casi-ordenado -> inserción).** Doc §4.9. Descartado: solo mergesort.
23. **3 carpetas físicas `controller1` / `controller2` / `orchestrator` con shims.**
    `adapters`+`api`→`controller1`, `controller`→`controller2`, `game`→`orchestrator` (`main` queda como entry point); `models` sigue compartido. Las 35 rutas viejas quedan como alias (`sys.modules`, mismo objeto): `monkeypatch` y `pytest.raises` siguen viendo una sola clase y los 140 tests no se tocaron.
    Descartado: renombrar sin shims (rompía 47 imports) y `import *` en shims (duplicaba módulos).
24. **Cero acoples cruzados con inyección, sin cambiar comportamiento.**
    `gamelog.iniciar` formatea `#cripta …` local (C1 trata líneas como opacas, K3); `Fachada` recibe `orden_fn` y la Sesión le inyecta `vista_ordenada` de C1 (§4.1/§5.1); `bench` vive en el orquestador que sí puede ver ambos.
    Descartado: imports lazy cruzados (`controller`→`adapters` y viceversa).
25. **`consola.py` tenía `SyntaxError` (f-string con `\"` anidados): nadie la importaba.**
    Se destapó al moverla al orquestador; se reescribió la línea con comillas de distinto tipo (mismo texto). Sin esto `--jugar` nunca habría arrancado.
26. **Shims eliminados: solo quedan las 3 carpetas.**
    Tests y docs migrados a rutas canónicas; se borraron `adapters/`, `api/`, `controller/` y `game/`. Una sola fuente de verdad.
27. **Vista Pygame en `src/view/` (V-1..V-10) + `tests/test_vista.py`.**
    Solo importa `Sesion`; teclado, sprites con reemplazo, 4 capas, 7 pantallas, HUD y pausa con guardar/cargar. `--vista` en CLI y `pygame-ce` en requirements. Único test con API real: `test_api_real`, salteado salvo `CRIPTA_API_REAL=1`.
28. **Paquete offline demo (`scripts/exportar_paquete.py` → `paquete_demo/`).**
    Vuelca FakeProvider (6 salas, 15 fichas) al formato `OfflineBackend` (ojo: trampa usa `daño` en JSON). Permite rutina/consola/vista sin red ni presupuesto; victoria verificada con 0 realizadas.
29. **Prota PNG + animación Rojo/Azul (`assets/sprites/`, `SpriteManager`).**
    `Little Caesars Feliz` (quieto) / `Blink` (paso): alternan cada 2 ticks con salto de 3px; Oeste espeja. Sin PNG o sin display, fallback procedural: nunca rompe.
30. **Movimiento libre por la sala (vista, sin tocar reglas).**
    WASD mueve el sprite (sin coordenadas en el modelo); al pisar puerta abierta se cruza (reaparece por el lado contrario), cerrada avisa y pide E; recoger/atacar solo a rango por proximidad. La vida sigue bajando al entrar por trampas/turnos del motor.
31. **Revisita sin respawn (`movimiento.py`): la sala viva se reutiliza.**
    Antes cada entrada pedía la sala fresca y la sobrescribía (objetos recogidos reaparecían, enemigos revivían). Ahora solo se pide al proveedor la primera vez; además gasta menos presupuesto.
32. **Drenaje consume el turno-jugador (caminar sigue gratis).**
    El marcador de turno taponaba la agenda y los enemigos lentos jamás actuaban. Ahora se consume al llegar (§2.3) y contraatacan tras tus intenciones. Se probó y revirtió que caminar pasara el tiempo: costaba vida y rompía el balance.
33. **Oleadas: aparecen errantes que vagan y atacan (`enemigos.py` + `Fachada.avanzar`).**
    Evento `oleada` en agenda (serializable K2, determinista por azar+seq, tope 4 vivos, cada 3000 default e inyectable para tests). Deshacer la retira (`aparece`); guardado la conserva. Sin línea de bitácora nueva (K3 intacto). En vista: enemigos circulares con anillo e insignia "!" (items y jugador siguen cuadrados/PNG).
34. **Patrullaje visible + alcance (vista): los guardianes no migran por diseño.**
    Deriva senoidal del slot (misma geometría para dibujar y proximidad) y marco verde al estar a rango de ataque. El combate ya funcionaba; faltaba verlo.
35. **Enemigos por todo el mapa: vecinas precargadas dormidas + velocidad real al activar.**
    Al armar una sala se resuelven en el mismo lote sus vecinas del plano (el contenido ya venía con el lote de 10; las fichas van en lotes de catálogo): entran al modelo como `SalaViva` dormidas, así errantes/rastreadores pueden cruzar el mapa sin despertarlas (§2.4) y sin inflar `salas_visitadas`/puntaje (§2.12). `intentar_mover` registra siempre la visita (las vecinas ya están en `estado.salas`) y pasa el catálogo a `activar_sala`, que antes activaba a todos con velocidad 5. El guardián sigue sin migrar: ese es su comportamiento.
    Descartado: pedir contenido nuevo por vecina en cada paso (más presupuesto y sin ventaja) y despertar la vecina al precargarla (rompe §2.4 y el puntaje).
36. **Trampas con daño, veneno o quemadura; también se pisan caminando.**
    `Trap` acepta `veneno` y `quemadura`/`fuego` opcionales (`daño` ya era tolerante). El motor aplica el daño y los pulsos: veneno 80×5 = 400, que el antídoto corta; quemadura 80×3 = 240, que el antídoto no cura. La vista envía `pisar <instancia>` al pasar por encima de una armada (una vez hasta salir del radio) además del disparo al entrar (§2.10); la intención también está en la consola de la fachada y de la sesión. Deshacer restaura vida y efectos y cancela los pulsos programados.
    Descartado: solo daño base (el pedido era envenenar/quemar) y redisparar cada frame encima de la trampa (spam de daño).
37. **Salas oscuras iluminadas con antorcha (offline y criptas de la API).**
    La sala acepta `oscura`/`oscuridad` en el esqueleto o en el contenido y lo conserva `SalaViva`/guardado; `K5` expone `sala_oscura`. La vista dibuja un velo negro con halo alrededor del jugador y lo levanta mientras el efecto `antorcha` esté activo (en `paquete_demo` la antorcha dura 1200 para alcanzar la sala 3). La consola avisa de la oscuridad y cómo encender una antorcha.
    Descartado: oscuridad solo decorativa de la vista (no servía para criptas de la API) y velo sin halo (no se podría jugar).
38. **Diagonal normalizada en la vista: el sprite se mueve igual de rápido en todo sentido.**
    El loop llamaba `_paso_libre` una vez por tecla sostenida; con dos ejes el sprite avanzaba √2. Ahora junta el vector de las teclas sostenidas (dedup W/↑, opuestas se cancelan) y `_mover_libre` lo normaliza antes de mover; `_revisar_puerta`/`_revisar_trampas` corren una sola vez por frame. Prueba: `test_movimiento_diagonal_normalizado`.
    Descartado: escalar por 1/√2 solo al detectar dos ejes (misma física, pero duplicaba la lógica de paso y los chequeos de radio).
39. **Feedback de daño y ataque en la vista: tinte rojo + sacudida; estela o embestida.**
    Al bajar la vida (`dano_ttl`) el sprite se multiplica a rojo (`capas._tinte_rojo`) y tiembla con patrón fijo de 6 offsets; al atacar, si hay arma visible se dibuja una estela de espadazo (`capas.dibujar_tajo`: arcos blancos por facing que barren y se desvanecen) y si no, el sprite embiste hasta 11 px hacia la dirección del golpe. Todo dibujo local de la vista (decisión 30): el motor y K5 no cambian; dura ~12 frames y expira solo. Pruebas: `test_dano_tinte_y_sacudida`, `test_ataque_embiste_siempre_y_taja_con_arma`, `test_tajo_estela_visible_y_expira`.
    Descartado: teñir el frame cacheado in situ (rompe la caché de sprites) y animar con azar real (irreproducible).
40. **Espejo persistente y paso suavizado; arma y escudo siguen el mismo estado.**
    Al caminar al Oeste el sprite se voltea (`app.espejo`) y al mirar N/S ese volteo se conserva (antes N/S volvían a mirar a la derecha "de la nada"); el desplazamiento del paso ya no salta de eje porque `paso_push` se interpola (lerp 0.5) hacia la dirección visible. El arma y el escudo dejan de depender del facing crudo: se dibujan del lado que marca `espejo` (offsets fijos `capas.OFFSET_ESCUDO_LADO`/`OFFSET_ESPADA_LADO`), la espada se rota según el lado (`sprites.ANGULO_ESPADA` base ±45) y ambos tienen caché por lado; `espejo=None` deriva de `facing=="O"` por compatibilidad. Con esto desaparecen los parches `OFFSET_ESCUDO`/`OFFSET_ESPADA` por dirección, que hacían brincar el equipo de lado al cambiar de eje. Pruebas: `test_espejo_se_conserva_al_mirar_arriba_o_abajo`, `test_sin_brinco_al_cambiar_de_eje`, `test_espada_y_escudo_en_cache_por_lado`, `test_arma_y_escudo_se_dibujan_del_lado_del_espejo`.
    Descartado: seguir parcheando ángulos/offsets por dirección (el parche rebuscado que el jugador recuerda) y suavizar con azar.
41. **La embestida del ataque se dibuja siempre; con arma se suma a la estela.**
    Antes: con arma solo estela, sin arma solo embestida. Ahora `_empuje_ataque()` (extraído del bloque de `dibujar`) empuja el sprite hacia el golpe durante los 12 frames en ambos casos; con arma además se pinta la estela blanca (`tajo`). Así atacar se lee igual de fuerte con o sin arma, junto al destello del golpe (`golpe`). Prueba: `test_ataque_embiste_siempre_y_taja_con_arma`.
    Descartado: dejar la embestida solo sin arma (menos consistente) y quitar la estela con arma (peor feedback).
42. **Jingle al empezar la partida (guiño a Little Caesars) en `src/view/sfx.py`.**
    `Sonidos` inicializa `pygame.mixer` de forma perezosa y `jingle_inicio()` reproduce `assets/sfx/little_caesars_pizza.mp3`; se llama al entrar a jugar en `iniciar_partida` y `cargar_partida` (cada partida empieza con el guiño, también al retomarla). Sin audio, dispositivo o códec MP3 devuelve False y la partida sigue en silencio: misma filosofía que los sprites con fallback (decisión 29). Pruebas: `test_jingle_al_empezar_partida`, `test_jingle_sin_audio_no_rompe`.
    Descartado: `pygame.mixer.music` (streaming innecesario para un jingle) y fallar/avisar ruidosamente si falta el MP3.
43. **Icono de la ventana = el prota de paso (`SpriteManager.icono` + `set_icon`).**
    El App instala el mismo frame que anima el paso (`Little Caesars Blink.png` escalado a 48, `_jugador_frames[1]`) como icono de ventana, en vez del icono por defecto: personalidad temática sin assets extra. Si faltan los PNG cae al mosaico procedural (`sp.jugador`), igual que el resto de sprites. Pruebas: `test_icono_ventana_es_el_prota_de_paso`, `test_icono_fallback_sin_png`, `test_app_instala_el_icono`.
    Descartado: generar un .ico dedicado (mantenimiento extra; el sprite ya es la identidad) y dejarlo por defecto.
44. **El disparo de trampas se ve: chispazo en el puesto + aviso de origen.**
    El daño al entrar (§2.10) o al pisar una trampa rearmada llegaba sin pista visual ("recibo daño aunque no esté ni cerca"). Ahora la vista detecta las trampas recién disparadas diffeando el multiset de `foto.mensajes` contra la foto previa (el motor anota `efecto|trampa|<inst>`; verificado que funciona aunque el rearme ocurra antes de la foto) y pinta un chispazo naranja (`capas.dibujar_fuego_trampa`: anillo + rayos que se expanden y desvanecen, 12 frames) en el puesto de cada una; al entrar a sala, además, el toast dice "¡Trampa al entrar! −N de vida". Pruebas: `test_trampa_al_entrar_marca_chispazo`, `test_caminar_sobre_trampa_la_dispara` (ampliada). Ver DECISIONES 36 para el pisar dentro de sala.
    Descartado: diffear `armada` True→False (los pinchos rearman en 3 unidades: vuelven a estar armados antes de la foto y el cambio nunca se ve) y reubicar la trampa junto a la puerta (mentiría: la regla es de sala, puede haber varias trampas y no se sabe por qué puerta entras).
45. **Rework gráfico de menús y pantalla final: jerarquía visual, no listas de texto.**
    El inicio, la selección de cripta y el fin se redibujan con lenguaje gráfico del propio juego (mismo registro producto: una tipografía, escala fija): fondo damero crema, logo "CRIPTA" con sombra flanqueado por el escudo y la espada-pizza, el prota en grande (frame quieto, espejado) como ilustración, botones con insignia de tecla visible (Jugar en naranja lleno; Continuar deshabilitado con su motivo), tarjetas de cripta con puerta dibujada + número de salas y dificultad como 5 puntos de pepperoni, y pantalla final con banner ¡VICTORIA!/DERROTA, arte (prota teñido si cayó; botín al ganar), resumen etiqueta→valor sin solapes (los valores largos bajan de línea) y acciones 1/2. Además la bitácora se humaniza (`texto.humanizar`: "Te moviste al sur", "Se activó la trampa t3", "Un enemigo se movió") en el HUD y en el fin: ya no se ven líneas `10|abrir|jugador|E`. Teclas nuevas en fin: 1 = jugar de nuevo (misma cripta si se conoce; si no, selección), 2/Esc = menú; `App` recuerda `cripta_actual` y limpia `reporte` al iniciar/cargar.     Todo el cromo va a escuadra (rectángulos duros, sin radios: insignias de tecla cuadradas, pepperoni cuadrado y pizza cuadrada en la carga), coherente con el pixel-art del juego. Todo es dibujo local (decisión 30): motor y K5 intactos. Pruebas: `test_dibujar_en_todas_las_pantallas`, `test_humanizar_bitacora`, `test_fin_teclas_jugar_de_nuevo_y_menu`; `test_pantallas`/`test_pantalla_fin_victoria_y_derrota` ampliadas (3 columnas, envoltura de nombres).
    Descartado: mantener listas de texto (lo que había) y mostrar rutas/diccionarios crudos al jugador.
    Arranque arreglado después del rework: `main` llamaba `listar_para_seleccion` al iniciar y, con una sola cripta (online y offline listan una), saltaba directo a la partida sin menú. Ahora `VistaApp.preparar_menu` carga las tarjetas dejando visible el menú principal y "1 Jugar" lleva a la selección; prueba `test_arranque_abre_en_el_menu_principal`.
46. **Enemigos con regeneración de catálogo (§2.10): pulso cada 200 con tope vida_max.**
    La spec permitía "un enemigo que declare regeneración" y el motor ya tenía ejecutor y rama de agenda, pero nada la agendaba: `Enemy` no parseaba el campo (`src/models/catalog.py`). Ahora `Enemy.regeneracion` (opcional, acepta `regeneracion` o `regen`) se normaliza a entero >0 o None; `enemigos.regeneracion_de` lo lee y `activar_sala` programa el primer pulso a `ahora + REGENERACION_PERIODO` al despertar la sala (junto al turno, con el catálogo real, como la velocidad de la mejora 35). La rama `regeneracion` de `Fachada.avanzar` ya reprogramaba si seguía vivo; ahora además apila el seq del siguiente pulso en su inversa, así el pergamino corta la cadena (antes quedaba un pulso huérfano). `jefe-cripta-01` del fake declara `regeneracion=2` (80 de vida) y `paquete_demo/` quedó regenerado con el campo. Pruebas: `test_enemigo_con_regeneracion_se_cura_con_tope`, `test_deshacer_regeneracion_corta_pulsos`.
    Descartado: regeneración solo para el jugador (la spec la declara por enemigo) y pulsos no reversibles (rompían §2.11).
47. **La embestida enemiga también se ve: el agresor se lanza hacia el jugador.**
    El contraataque llegaba solo como toast + tinte rojo propio; el enemigo culpable no se distinguía de los que estaban quietos. Ahora la foto expone `activa` por enemigo (dormido vs despierto, sin romper K5) y el App diffea la bitácora (`dano|<instancia>|N`, la única fuente de esa línea es `ataque_enemigo`) contra la foto previa: la instancia agresora entra en `app.golpes` (12 frames) y `capas.dibujar_actores` la embiste hasta 10 px hacia el jugador, con destello rojo al impactar — mismo lenguaje que la embestida del prota (decisión 41) y mismo pipeline que el chispazo de trampas (decisión 44). Prueba: `test_embestida_enemiga_marca_al_agresor` (espera turnos del guardián e1-1 en la sala 1 y verifica marca + dibujo).
    Descartado: animación perpetua de ataque en enemigos (sin turnos expuestos en K5 mentiría) y depender del toast de daño (no dice quién golpeó).
48. **Menús con el arte nativo del prota: nítido, no el frame reducido.**
    En partida el PNG se reduce a TAM (nearest, look retro, decisión 29), pero los menús reescalaban ESA imagen ×3-4 y el prota se veía pixelado teniendo 117×161 de arte real. `SpriteManager.jugador_grande(escala, espejo)` parte del PNG nativo, lo escala **nearest** por defecto (sin antialiasing, coherente con el resto; `suavizado=True` cambia a smoothscale) y cachea por (escala, espejo); `pantallas._prota` lo usa (inicio 1.9×, fin 1.4×) con fallback al frame de juego si falta el PNG. Prueba: `test_jugador_grande_nativo_y_cacheado`.
    Descartado: subir TAM del juego (rompe la escala Rojo/Azul del sprite en sala) y smoothscale (antialiasing: el usuario lo rechazó).
49. **HUD de partida: canvas 4:1 sobre banda de información; fuera la bitácora.**
    La sala ocupa la zona superior centrada en el eje horizontal (ancho 4:3 respecto a su alto, con 8 px de padding), y una banda inferior de ~1/5 del alto útil guarda, tras una línea dorada, tres filas: contadores (vida con barra, ATK/DEF/VEL, efectos, pergaminos), mochila horizontal (marco dorado = seleccionado, "E" = equipado) y los controles de partida siempre visibles (`pantallas.CONTROLES`: mover, abrir, atacar, recoger, mochila, equipar, usar, pausa). El panel de bitácora desaparece: el jugador ya recibe lo importante por el toast y los resaltes (`dibujar_mensajes` queda en `ui.py` sin uso en partida). `area_sala` centraliza el canvas; el toast de avisos se apoya sobre la línea para no tapar los contadores. Prueba: la suite de vista (`test_pantallas`, embestida) sigue verde.
    Pendiente decidido: los assets de cajas (Pizza Box) se integrarán después de validar la distribución.
50. **Caja de pizza como identidad: Box de fondo y tapa que abre el menú.**
    `assets/sprites/Pizza Box/` trae 7 PNG de 512² alineados en el mismo lienzo: Box (caja abierta) y Lid Stage 1-6 (la tapa girando). (a) El canvas de sala usa `SpriteManager.caja_fondo(w, h)`: recorta el arte útil de Box y lo escala nearest hasta cubrir el área (sin deformar, `None` -> damero de respaldo en `capas.dibujar_fondo`). (b) El menú de inicio compone cuerpo + título + tapa en el mismo rect: la tapa cerrada (stage 1) esconde "CRIPTA"; `stage_caja(apertura)` avanza 1->6 (30 frames de espera, 10 por stage) y la apertura lo revela; en stage 6 el título queda dentro de la caja abierta. `VistaApp.menu_ttl` cuenta frames y `_abrir_menu()` (única puerta al inicio) reinicia la animación. Botones del menú pasan a fila horizontal para dejar la caja centrada. Pruebas: `test_caja_pizza_abre_por_stages`, `test_caja_fondo_cubre_area_y_assets`, `test_menu_animacion_se_reinicia`.
51. **El campo de juego es el hueco del sprite; la caja acompaña todos los menús.**
    El lienzo de 512² de la caja deja libre el recuadro (110,110) de 290x290; `zona_caja(rect)` y `capas.rect_caja(area)` (inversa) convierten entre el arte y el campo. `VistaApp.area_sala` ya no elige un 4:3 a ojo: maximiza la caja dentro de la zona útil y devuelve su hueco (cuadrado, centrado en el sprite), de modo que el contenido nunca pisa los bordes del arte (prueba `test_zona_caja_cuadrada_y_rect_inverso`). Además, selección, carga, fin, pausa, error y versión pintan la caja tenue (`pantallas._caja_de_fondo`, alfa 64, mismo rect que el menú) para que el zoom menú→juego tenga continuidad visual. La línea del HUD pasa a colgar del rect del arte (`rect_caja(area).bottom + 2`).
52. **Menús unificados (caja arriba, opciones abajo), ventana 1024×800 y zoom sin doble caja.**
    (a) Selección, carga, fin, error, versión y pausa adoptan el layout del inicio: `pantallas._caja_menu(sup, sprites, titulo, color, sub, stage)` dibuja la caja del menú (290×380, centrada arriba) con el título y su subtítulo DENTRO del arte y el contenido debajo; `rect_caja_menu` es además el origen del zoom. La caja tenue de la decisión 51 (`_caja_de_fondo`, alfa 64) se elimina: todos los menús muestran la caja real, con la tapa cerrada en stage 6 (y en el inicio, su apertura animada). La selección usa tarjetas compactas (`_tarjeta_cripta`: insignia, nombre a 1-2 líneas, puerta + «N salas», dificultad como pepperoni) en 2 columnas (≤4 criptas) o 3. (b) La ventana por defecto pasa de 960×640 a 1024×800: con el hueco del sprite en (110,110) de 290×290, el canvas gana a ~436² (≥ al 4:3 anterior) sin apretar el HUD; `area_sala` baja el padding a 20 y los botones/prota del fin y el inicio se calculan con el ancho real (centrados), no con coordenadas fijas de 960. (c) El zoom menú→partida (decisión 51) dibujaba la caja interpolada SOBRE el canvas del juego ya pintado: dos cajas a la vez. Ahora `pantalla_juego(..., mostrar_canvas=False)` omite fondo y actores mientras `zoom_ttl` corre — solo se ve la caja del menú encogiendo/interpolando — y al terminar la animación el siguiente frame pinta la vista de juego completa (intercambio de versiones en el mismo rect final, sin salto). Pruebas: la suite de vista completa (221) sigue verde, con los renders de menú y del zoom (`/tmp/opencode/zoom_*.png`) verificados a mano.
    Descartado: parchear `_dibujar_zoom` con recortes del canvas (seguirían viéndose entidades tras la caja en vuelo) y agrandar la ventana a 4:3 (el hueco del sprite es cuadrado; 1024×800 ya supera el canvas anterior).
53. **Botones de menú también con ratón: hover + clic = la misma tecla.**
    Todos los menús publican sus hotspots `(rect, tecla)` desde `pantallas` (inicio, selección por tarjeta, pausa, fin, error y versión) y `VistaApp.dibujar` los guarda en `self.hotspots`; `manejar_clic(pos)` busca el rect y despacha `manejar_tecla(tecla)`, así el ratón reusa TODA la lógica de teclado (nada de acciones duplicadas) y respeta los deshabilitados (Continuar sin guardado no tiene hotspot). `boton(...)`/`_tarjeta_cripta` aceptan `resaltado` (ratón encima) y aclaran el panel (naranja más claro en el primario, crema en el resto). Error y versión, que solo tenían el pie "Esc vuelve al menú", ahora muestran un botón real "Volver al menú" (insignia Esc) para que el jugador de ratón no quede atrapado. `ejecutar` atiende MOUSEMOTION (hover) y MOUSEBUTTONDOWN de botón izquierdo, con el mismo try/except que las teclas. Prueba: `test_raton_interactua_con_botones_de_menu` (hover cambia píxel, clics en inicio/selección/pausa/error; Continuar deshabilitado sin hotspot).
    Descartado: sintetizar eventos de teclado (frágil para las pruebas) y un mapa de acciones paralelo al de teclas (doble mantenimiento).
54. **Almacén de fichas en disco (`almacen_fichas.py`): desalojar de la LRU ya no pierde la ficha (§4.4).**
    Archivo append-only con magia `CRIPTAFX\0` + versión de formato + registros largos pickleables; índice hash propio id→offset (offset al inicio del registro). `obtener` lee solo esa ficha; el RoomLoader recupera de memoria→almacén→red y reinserta en la LRU; la versión de catálogo invalida y trunca al próximo guardado. En tests/offline sin ruta no hay almacén (no se inventa caché en disco).
    Descartado: releer de red al desalojar (gastaba presupuesto con fichas ya conocidas) y archivo con pickle completo reescrito entero (O(catálogo) por ficha nueva).
55. **Pin de caché acotado al estado real de la partida (§4.4).**
    `ProveedorSesion._armar` ya no fija todo lo que arma: la Sesión recalcula `_fijar_fichas_en_uso` (enemigos vivos, suelo, trampas e inventario de la sala actual + equipo) cada vez que el estado cambia. Antes el pin cubría el catálogo entero y con el tope de 25 la LRU no podía desalojar nada.
    Descartado: pin por sala visitada (crecía sin tope y bloqueaba el desalojo legítimo).
56. **Buffer circular propio de 20 mensajes (`buffer_circular.py`) (§4.8).**
    Arreglo fijo con índice de escritura módulo 20: agregar O(1) sin desplazar nada y memoria constante; `ultimos(k)` para la foto/consola. La decisión 18 decía "20 circular" pero la implementación recortaba listas; esto la hace real.
    Descartado: `collections.deque(maxlen=20)` (correcto pero ajeno a la restricción de estructuras propias) y recorte `[-20:]` en cada foto (copia por mensaje).
57. **Equipar arma y armadura ya no anula la otra ranura (§2.7).**
    `fachada.equipar` guardaba una sola ranura; ahora desequipa solo la del mismo tipo y ambas conviven, con las dos incluidas en el pin de equipo. Test `test_equipar_arma_y_armadura_conviven`.
    Descartado: una ranura de equipo genérica (perdía el bonus de la otra pieza al alternar).
58. **Vista ordenada del inventario también en consola y vista (§4.5/§10.2).**
    `Sesion.inventario_ordenado(criterio)` delega en el mergesort inyectado; la consola acepta `inventario [nombre|peso|valor]` y la vista cicla criterios con C (orden real → nombre → peso → valor) marcando "E" las equipadas en cualquier orden. Antes `vista_ordenada` de C1 existía sin uso en la interfaz.
    Descartado: ordenar en la vista/consola (violaría §4.9: el ordenamiento evaluado vive en C1, C2 lo recibe inyectado).
59. **Agenda con doble enlace e índices propios; antídoto O(k) (§4.1/§4.8).**
    Ver §4.1 de la parte A. `usar_antidoto` pasó de `cancelar_donde` (barrido) a `cancelar_tipo("veneno")`; `deshacer` cancela por seq en O(1). El bench `agenda_cancelar_barrido_20k` conserva la alternativa descartada medida.
    Descartado: montículo binario (cancelaciones frecuentes) y mantener el barrido (3× más lento ya con 20k eventos).
60. **Cero `sorted()`/`sort()` en `src/` para los ordenamientos evaluados (§4.9).**
    Guardado (índice de salas), agenda reconstruida, padrón/vecinas de enemigos y salidas del mapa usan mergesort de C1 (C1/orquestador) o la inserción local de C2 (`orden_local`, sin importar C1). El único `sorted(` que queda en el repo es la mención en el docstring de `mergesort.py`.
    Descartado: dejar `sorted()` en sitios "no evaluados" (el grep del evaluador no distingue).
61. **Bench ampliado: almacén, buffer, cancelación indexada vs barrida y ciclo completo (§5.3/§8).**
    `--bench` ahora mide recuperación del almacén, buffer de 100k mensajes, `cancelar_tipo` contra `cancelar_donde` y un ciclo de partida de punta a punta (iniciar + ruta de victoria con caché y almacén en disco) con backend sintético propio, sin depender de `paquete_demo/` (fixture de tests).
    Descartado: medir el ciclo con la red real (no reproducible) y depender del paquete offline (el bench debe correr siempre).
62. **SFX a volumen bajo y sprites de items por grupos de nombre (view).**
    `sfx.VOLUMEN = 0.1` aplicado con `set_volume` en cada reproducción (0.5 y 0.25 seguían fuertes: pygame mide amplitud lineal). `sprites.py` clasifica por palabras clave (`_CLAVES_POCION`, `_ARMA`, `_ARMADURA`, ...): TODAS las pociones y las curas (antídoto) comparten `pocion-salud.png` (también las de velocidad: el frasco no revela el efecto), protección (coraza, peto...) usa `escudo.png`, armas (mandoble, daga...) usan `espada.png`, `llamas-01` dejó de salir magenta (trampa). TODOS los enemigos comparten el sprite `enemigo-errante.png` (el comportamiento solo cambia la IA; el fallback sin assets sigue coloreando por comportamiento). Se corrigió un "espada" duplicado en las claves.
    Descartado: un PNG por id (imposible con el catálogo abierto de la API), colores de respaldo por hash (el usuario pedía arte real por familia) y mantener la poción de velocidad con PNG propio (el usuario pidió frasco único).
63. **Retroceso real por intervalos: el tope 5 cuenta acciones del jugador, no eventos (+ un solo marcador de turno).**
    El tope contaba ENTRADAS: cada pulso de veneno, rearme o turno gastaba cupo, así que un intervalo largo podía expulsar la acción del jugador de la ventana y `deshacer` moría con "Nada que deshacer." (o revertía eventos sueltos sin su acción). Ahora `PilaDeshacer` cuenta intervalos: cada acción de `ACCIONES_JUGADOR` (mover, abrir, esperar, daño, recoger, soltar, equipar, pociones…) abre uno — "trampa" no: pertenece al intervalo en que se pisó; al superar `TOPE=5`, `_olvidar_mas_vieja()` corta en la 5.ª frontera y descarta la acción más vieja CON todo su intervalo. Cada frontera guarda reloj/acciones/rastro de antes y el bloque común de `aplicar_inversa` los restaura; los inversos devuelven los turnos consumidos (`turno_antes` reinsertado con su `(t, seq)`), `derrotados_antes`, los contadores de veneno/quemadura, sala/rastro/visita (durmiendo lo despertado y cancelando TODOS sus turnos pendientes, no solo el de activación) y la oleada (`oleada_antes` + cancelación de la reprogramada). `Agenda.reinsertar(t, tipo, datos, seq)` conserva `(t, seq)` sin tocar el contador interno. De paso se corrigió la cadencia del reloj (§2.3): el marcador del jugador se acumulaba y `_programar_turno_jugador` ahora garantiza A LO SUMO un marcador pendiente (cancela los anteriores; con save, `inicial=True` respeta el cargado), y `Fachada.deshacer` reinserta el suyo en el instante rebobinado con seq `-1` para que el drenaje lo consuma primero en empates y el estado quede congelado justo ahí. Deshacer no consume azar ni reescribe la pila: la paridad del replay se mantiene.
    Descartado: subir el tope (seguiría desalojando la acción), etiquetar cada entrada con su acción (mismo corte, más contabilidad) y rebobinar el azar (no lo consume el retroceso).
    Pruebas: `test_pila_tope_por_intervalos_descarta_solo_el_mas_viejo`, `test_agenda_reinsertar_conserva_t_y_seq`, `test_deshacer_sin_accion_no_consume_pergamino`, `test_deshacer_esperar_es_accion_y_restaura_reloj`, `test_deshacer_devuelve_sala_y_restaura_intervalo`, `test_pergamino_devuelve_a_la_sala_anterior` y la de aceptación `test_seis_acciones_deshacer_cinco_vuelve_al_estado_de_la_primera` (6 acciones, 5 retrocesos y el retrato observable queda idéntico al de una sesión que solo jugó la 1.ª). `test_oleada_deshacer_la_retira` y `test_deshacer_regeneracion_corta_pulsos` se adaptaron (abren intervalo con `esperar`).
64. **El pergamino se ve: rebobinado violeta y el prota reaparece junto a la puerta.**
    El retroceso ya redibujaba todo (§7) pero el cambio de sala era un salto seco. `capas.dibujar_rebobina(sup, area, fase)` pinta 18 frames (`app.REBOBINA_FRAMES`) de anillos violeta (`paleta.MAGIA`) que se expanden hacia afuera con velo y chispas girando al revés sobre la caja de la sala; es determinista (sin azar), se recorta al arte (el HUD queda legible) y `VistaApp.enviar` lo dispara SOLO si `deshacer` fue aceptado (los rechazos no destellan), apagándose solo en `dibujar()`. Si el retroceso cambió de sala, `_aparecer_tras_retroceso(sala_antes)` busca la puerta de la sala actual cuyo destino es la abandonada y planta al prota de ese lado del vano (`JUNTO_A_PUERTA`, con `OPUESTA` que ahora comparte `_revisar_puerta`), con `en_puerta=True` para no recruzar por proximidad y la animación de paso en cero; retrocesos dentro de la misma sala conservan la posición.
    Descartado: fantasma del prota saliendo de la sala (no se guarda la posición previa; el anillo + velo ya leen "rebobina"), sonido sintético (sin asset y la vista no usa numpy) y destello también en los rechazos.
    Pruebas: `test_rebobina_anillos_violeta_y_apagado` (pinta en violeta, fase 0 no pinta, misma fase = mismos píxeles) y `test_deshacer_rebobina_y_reaparece_en_la_puerta` (dispara solo al aceptar, posición junto a la puerta, expira solo); fotogramas renderizados a mano (`rebobina_*.png`).
65. **`usar <pergamino>` delega en `deshacer` (§10.2): antes moría con "No se puede usar así."**
    `Fachada.usar` solo ruteaba poción/antídoto/antorcha; el pergamino exigía el comando `deshacer` (tecla U en vista) y `usar pergamino-01` caía al mensaje genérico. Ahora la clase `pergamino_retroceso` (o id con "pergamino"/"retroceso") llama al mismo `deshacer()`, así R sobre el pergamino también rebobina. Prueba: `test_usar_pergamino_delega_en_deshacer`.
    Descartado: dejar solo el comando `deshacer` (contradice §10.2 "usar un pergamino de retroceso" como acción de interfaz).
66. **Deduplicar lotes sin `dict` (§7): helper `unicos` propio.**
    `dict.fromkeys(ids)` deduplicaba ids antes de pedir fichas/lotes (room_loader, endpoints, offline, sesión, bench, fakes de tests) y era la única aparición de `dict` fuera de (de)serialización JSON. Reemplazado por `src/controller1/unicos.py` (lista de vistos, búsqueda lineal; los lotes son chicos). Los `dict` que quedan en `src/` son solo para leer/escribir JSON (contratos del API, `a_dict`/`from_dict`, `catalogo.json`) y los mapas del propio modelo K2 (`estado.salas`, `efectos`), que son el formato de estado serializado, no índices internos: los índices evaluados (caché LRU, tabla hash, agenda, buffer) son implementaciones propias en `src/controller1/`/`src/controller2/`.
    Descartado: dejar `dict.fromkeys` (un grep del evaluador lo marca como dict-tabla) y migrar los mapas del modelo a estructuras propias (riesgo alto en save/replay sin beneficio evaluable; ya justificado en la decisión 4).

67. **Fundamentos neutrales de002: índice hash, heap y metadatos inmutables.**
    Problema: consultar registros por IDs dispersos/extremos y priorizar búsquedas
    sin importar C1 desde C2 ni sustituir estructuras evaluadas por bibliotecas.
    `src/estructuras/tabla_indice.py` usa cubetas y cadenas propias con hash
    determinista de enteros/extremos, carga máxima0,75 y duplicación con rehash.
    No reserva hasta el ID máximo. `monticulo_minimo.py` usa heap binario sobre
    list y secuencia de inserción para empates, sin comparar los valores.
    `src/models/conocimiento.py` ofrece DTO congelados con salidas en tuplas,
    costos positivos e IDs/direcciones estrictos, sin estado mutable remoto.

    Alternativas: la tabla de C1 está acoplada al LRU y cruzaría la frontera de
    capas; una lista lineal encarece consultas por ID; un arreglo por ID máximo
    desperdicia memoria con IDs dispersos. Para prioridades, una cola lineal
    encarece selección/extracción, y heapq sustituiría una estructura evaluada.
    Se mantienen los componentes separados para su futura integración.

    Complejidad teórica, para claves de tamaño acotado: índice con consulta
    esperada O(1), inserción esperada amortizada O(1), rehash O(capacidad+n),
    iteración O(capacidad+n) y memoria O(capacidad+n). No reduce capacidad al
    borrar, por lo que esta depende del máximo número de registros almacenados.
    Heap: insertar/extraer O(log n), memoria O(n). Los DTO tienen como máximo
    cuatro salidas por sala. Límites: colisiones adversarias pueden degradar la
    consulta; las expansiones deben incluirse al medir revelación amortizada.

    Evidencia funcional:42 pruebas nuevas aprobadas; regresión total298
    aprobadas/1 omitida con SDL dummy (comandos y resultados en
    `specs/002-niebla-ir-a/quickstart.md`). Aún no hay mediciones de rendimiento,
    comparación empírica con las alternativas ni aceptación de5 ms: pendientes
    de T044–T048. No se modificaron modelos ponderados de001, contratos vigentes,
    guardado o replay; la integración permanece condicionada a T001.

68. **Terreno y cazador: montículo mínimo propio para Dijkstra acotado, costos en salidas e invalidación estricta de rutas.**
    Problema: perseguir al jugador por la ruta de menor costo de tránsito usando solo salidas abiertas en ese instante (FR-CAZ-05, FR-CAZ-06) sin superar 20 ms con decenas de cazadores activos (FR-CAZ-14) y asegurando equivalencia exacta con un cálculo desde cero (FR-CAZ-11) y desempate por menor id de vecina (FR-CAZ-09). PROHIBIDO usar heapq, deque, set o dict como estructuras auxiliares evaluadas.

    Alternativas y justificación:
    (a) Lista enlazada ordenada (como la agenda de eventos): aunque sacar el mínimo es O(1), relajar aristas e insertar distancias tentativas exige barrido lineal O(V). Para Dijkstra sobre V salas y E aristas, la complejidad total degenera a O(V^2 + E*V) = O(V^2). En una cripta de 1 000 salas requiere ~1 000 000 de operaciones elementales, superando 100 ms y violando FR-CAZ-14. Descartada por lenta para grafos medianos y grandes.
    (b) Montículo binario mínimo propio (`MonticuloMinimo`): implementado en `src/estructuras/monticulo_minimo.py` sobre un arreglo contiguo con flotar/hundir y secuencia de inserción para desempate estable. Inserción y extracción en O(log V), con complejidad total Dijkstra O((V + E) log V). Para 1 000 salas toma ~50 000 operaciones (>20× más rápido que la lista enlazada). Combinado con `TablaIndice` propia para etiquetas de distancia O(1), garantiza ciclos <= 20 ms. Elegida.

    Estrategia de cálculo e invalidación:
    - Búsqueda acotada por rango (individual): Dijkstra desde el cazador que poda aristas con costo acumulado > rango; acota el trabajo a la bola local B(u, rango) y hace el tiempo independiente del tamaño total de la cripta (FR-CAZ-14).
    - Cálculo compartido (inverso): Dijkstra desde el jugador acotado por max(rango), aprovechando que los costos son simétricos (FR-CAZ-01). Resuelve a decenas de cazadores simultáneos en un solo barrido. Ambas opciones producen idéntica decisión y se comparan en `--bench` (FR-CAZ-15).
    - Invalidación de ruta: se invalida inmediatamente si el jugador cambia de sala o si cambia cualquier puerta (`puertas_version`). Muerte de actores o cambios de velocidad no invalidan porque no alteran la topología ni los costos de salida (FR-CAZ-03).
    - Desempate: entre vecinas v con costo(u, v) + dist(v, jugador) == d, se elige min(v.id) de forma determinista (FR-CAZ-09).

    Complejidad teórica:
    Búsqueda acotada: O((V_R + E_R) log V_R) donde V_R es el número de salas dentro del rango. Memoria O(V_R). Verificación de validez de caché: O(1). Desempate entre vecinas: O(grado(u)) = O(1).

    Límites y medición:
    En criptas disconexas o cuando d > rango el cazador espera con costo 100. La justificación empírica completa de las estructuras y estrategias se mide con la suite `--bench` (1 vs 50 cazadores, rango pequeño vs grande, individual vs compartido, y montículo vs lista enlazada) según FR-CAZ-15.

    Evidencia empírica (`--bench`):
    - Ciclo con 50 cazadores concurrentes: `cazadores_50_ciclo` = 0.000501 s (0.50 ms) vs `cazador_1_ciclo` = 0.000004 s (4 µs), cumpliendo con creces el límite de SC-CAZ-01 (<= 20 ms).
    - Independencia del tamaño de la cripta con rango acotado: `cazador_rango_pequeno_10k` = 0.000001 s (1 µs en 10 000 salas) vs `cazador_rango_pequeno_100` = 0.000001 s (1 µs en 100 salas), confirmando SC-CAZ-02.
    - Estrategia compartida vs individual: `cazador_compartido` = 0.000221 s vs `cazador_individual` = 0.015978 s (aceleración de ~72× al resolver en bloque desde el jugador).
    - Reutilización de rutas con invalidación estricta: `cazador_reutilizacion` = 0.000286 s vs `cazador_recalculo` = 0.010815 s (~38× más rápido preservando equivalencia observable exacta).
    - Sensibilidad a mutación de puertas: `cazador_puertas_estables` = 0.000020 s vs `cazador_puertas_inestables` = 0.006242 s (invalidación O(1) vía `puertas_version`).
    - Estructuras evaluadas: `cazador_monticulo_minimo` garantiza O((V+E) log V) y estabilidad por secuencia de inserción, sin dependencias prohibidas.
    - Validación funcional: 19 pruebas de capacidad 001 aprobadas al 100% (cubriendo los 7 casos del Apéndice B y aclaraciones), regresión completa de 373 pruebas aprobadas (1 omitida por SDL).

## C. Parte 2 — Niebla e «ir a» (002), 2026-11-09

**Problema.** La precarga de salas es infraestructura y no conocimiento. El
viaje debe usar solo salas exploradas y memoria de puertas, aceptar cancelación
entre movimientos y permitir invertir cada paso sin copiar el mapa entero.

**Alternativas.** Filtrar salas cargadas filtra infraestructura; las visitas
físicas no representan la antorcha. Una copia por acción incumple la restricción
de memoria. BFS ignora costos; compartir resultados de cazadores mezcla puertas
vivas con memoria del jugador. Se comparan índice propio frente a búsqueda
lineal y heap propio frente a cola de prioridad lineal en los benchmarks.

**Elección.** `MapaConocido` con tablas hash propias redimensionables y registros
inmutables; observación presencial separada de revelación remota; cambios
antes/después por registro adjuntos a la inversa causal. Dijkstra neutral con
heap e índice propios calcula cada paso sin caché de rutas, usando únicamente
adyacencia conocida. Sesión ejecuta un movimiento ordinario y drena una vez;
la UI espera al menos150 ms reales y procesa la entrada antes del siguiente paso.
El receptor opcional para004 recibe deltas antes del descarte por tope cinco;
002 no retiene la historia completa ni elige K.

**Complejidad.** Índice: consulta esperadaO(1), inserción esperada amortizadaO(1),
rehashO(n) al duplicar por carga0,75. DijkstraO((V+E)log(1+E)), espacioO(V+E)
en la región conocida descubierta. Proyección completaO(VlogV+E) con mergesort;
la UI la reutiliza por revisión. Revelación ordinaria depende de registros
revelados/observados y sus salidas acotadas a cuatro; las expansiones se cuentan
en el costo amortizado, no se esconden en las mediciones.

**Validación funcional.** 415 pruebas aprobadas/1 omitida (HTTP optativo),
5,33 s, con SDL dummy. Se corrigieron cruce visual automático sin reposición,
consultas de mochila que cancelaban el viaje y copia superficial de la caché
LRU candidata. Consola admite reloj/lector inyectados y muestra costos y memoria
de puertas; EOF/KeyboardInterrupt cancelan. Guardado v3 y deltas sobreviven al
roundtrip; las cargas corruptas preservan la sesión y el viaje. Evidencia y
límites en `specs/002-niebla-ir-a/quickstart.md`.

**Límites.** La entrega aislada no acredita costos/tiempos ponderados ni simetría
física de001, historia004 o referencia oficial de5 ms.
El recorrido con comandos por stdin y render headless no sustituye una sesión
manual completa. §5.6 y la elección de K siguen fuera del alcance de002.


**Fuentes y concordancia con el plan.** [Spec002](specs/002-niebla-ir-a/spec.md)
y [plan002](specs/002-niebla-ir-a/plan.md). El diseño final conserva la elección
del plan. Se eliminan consultas redundantes de adyacencia: cada destino se busca
una vez por salida, conservando N,S,E,O. El enunciado íntegro aportado por el
usuario, `docs/Cripta Parte II.md`, quedó leído y contrastado el2026-11-09;
se retira el límite anterior por fuente P2 ausente, sin extenderlo a una supuesta
entrega de la referencia oficial de rendimiento o de001/004.


## Mediciones finales de002 — 2026-11-09

Comando ejecutado con salida0: `.venv/bin/python -m src.main --bench`.
Informe íntegro: [002-niebla-2026-11-09.json](docs/mediciones/002-niebla-2026-11-09.json).
Semilla20261106; Python3.12.3, Linux, Intel Core i7-1185G7@3GHz. El informe incluye
SO, CPU, base Git, estado modificado y SHA256 de las fuentes medidas. No se
instancia vista ni red. Se conservaron todos los benchmarks anteriores.

La matriz final contiene36 cargas: tres tamaños, cadenas/mallas/empates,
conocimiento parcial/completo y puertas recordadas estables/desactualizadas.
Los costos recíprocos son iguales y el grado es≤4. Cada carga comprueba igualdad
de resultado entre heap y cola lineal antes de medir. El muestreo se ajustó a
1000/100/10 consultas y100/10/1 calentamientos para100/1000/10000 salas: el plan
original exigía1000 en todos los tamaños y resultó demasiado costoso. P2§6.3 no
fija ese número. Se publica el cambio; p95 con10 muestras es aproximado. Los
máximos observados son mediciones de esta ejecución, no garantías.

Ejemplo: malla completamente conocida, memoria estable, ruta del inicio al final:

| Salas | Consultas por alternativa | Heap mediana / p95 / máximo (ms) | Cola lineal mediana (ms) | Pico auxiliar heap (bytes) |
|---:|---:|---:|---:|---:|
| 100 | 1000 | 2.691 / 5.601 / 8.653 | 3.352 | 9280 |
| 1000 | 100 | 34.766 / 40.203 / 42.801 | 40.554 | 71964 |
| 10000 | 10 | 404.143 / 441.930 / 441.930 | 716.748 | 1413300 |

**Resultado de rendimiento.** En la matriz completa, el máximo del heap fue
23,142/86,251/452,053 ms para100/1000/10000 salas. Hubo581/1000/100 consultas por
encima de5 ms, sobre12000/1200/120 consultas respectivamente. Estas cargas
sintéticas no acreditan FR-NIE-19/SC-NIE-01. Falta la referencia oficial compatible;
no se declara cumplido el presupuesto. El heap reduce la mediana frente a la
cola lineal en la malla grande (404,143 frente a716,748 ms), con memoria auxiliar
similar. Se conserva la estructura prevista en el plan, sin afirmar que ello
resuelva todavía el límite temporal.

**Consultas y revelación.** Para100/1000/10000 salas, la mediana de consulta por
índice fue0,001004/0,001131/0,001652 ms; la alternativa lineal,
0,001573/0,029619/0,180993 ms. Revelar las mismas dos salas produjo siempre cinco
consultas y dos escrituras, sin rehash ordinario ni recorrido completo. Las
secuencias de100/1000/10000 altas incluyeron5/8/11 expansiones y186/1530/12282
registros movidos: ese costo no se excluye de la proporcionalidad amortizada.
El mapa completo se mide separadamente; su extracción y orden no se confunden
con una consulta puntual o revelación.

**Optimización y límites.** La adyacencia consultaba cada destino en cada una de
las cuatro vueltas por dirección; ahora filtra la dirección antes de buscarlo.
La prueba de operaciones confirma una consulta por salida y conserva el orden
N,S,E,O. La matriz final se ejecutó después de ese cambio. La matriz exhaustiva
inicial fue interrumpida y no tiene resultados agregados publicados; el piloto
dirigido anterior no es la referencia de esta tabla. No hay comparación temporal
antes/después controlada con la misma carga, por lo que no se atribuye una razón
de aceleración a la optimización. La justificación comprobada es reducir accesos
redundantes. La aceptación de tiempos ponderados001, historia004 y referencia
oficial permanece abierta. Esto no cierra§5.6 ni elige K.

## D. Línea de tiempo004 — 2026-11-10

**Problema y elección.** Consultar pasado sin alterar juego/undo, con hasta K
acciones de reconstrucción y memoria proporcional a los cambios. Se eligió un
diario de escrituras de C2: asignaciones y mutaciones de colecciones registran
ruta, presencia y valores antes/después. Las inserciones/borrados de listas
conservan solo el segmento afectado. La auditoría encontró que copiar las
inversas P1 directamente perdería RNG, pergaminos y cambios de agenda posteriores
al apilado. Se mantiene independiente la pila P1 de cinco intervalos y el
colector de conocimiento002.

Los checkpoints completos se crean al inicio y cada K acciones; la consulta
copia el checkpoint posterior más cercano o el estado actual y aplica deltas
inversos hasta el corte. Cortes/checkpoints se localizan por búsqueda binaria
propia, O(log A). El costo de reconstrucción depende del tamaño del estado y
los deltas de hasta K intervalos. El truncamiento trabaja sobre el sufijo
revertido y sus checkpoints, sin recorrer el prefijo histórico. El pergamino
conserva su ordinal separado y no cambia los contadores/exclusiones P1.

**Alternativas.** Snapshot completo por acción viola la restricción de memoria.
Reconstruir desde el principio evita checkpoints pero cuesta según la longitud
de la historia; la alternativa medida a continuación usa inversión desde el
estado actual sin checkpoints intermedios. Re-simulación desde un checkpoint
es válida pero volvería a ejecutar reglas y exigiría aislar proveedor/catálogo;
la inversión del diario reconstruye sin motor ni red.

**Medición principal ejecutada.** 5.000 órdenes `esperar` aceptadas mediante
Sesión y motor reales; tres salas hidratadas, sin enemigos/trampas, oleadas
fuera del intervalo medido, semilla20261110. Incluye agenda/seq, RNG serializado,
conocimiento y pila P1. 100 calentamientos +1.000 consultas por tiempo por K,
sin red ni render; mismos resúmenes en todas las variantes. Datos completos en
[004-historia-motor-2026-11-10.json](docs/mediciones/004-historia-motor-2026-11-10.json).
Python3.12.3, Linux, Intel Core i7-1185G7; detalles en el informe.

| K | Mediana ms | p95 ms | Máximo ms | Bytes checkpoints, JSON compacto | Memoria de estructura Python bytes | Máximo acciones reconstruidas |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 10 | 0,792 | 1,368 | 2,785 | 4.865.757 | 47.813.610 | 10 |
| **20** | **0,997** | **1,954** | **2,862** | **2.437.388** | **39.122.486** | **20** |
| 50 | 1,652 | 2,978 | 4,519 | 980.356 | 33.907.702 | 50 |
| Sin intermedios, K=5001 | 112,345 | 238,222 | 485,004 | 8.993 | 30.431.238 | 5.000 |

Se conserva **K=20** por reducir aproximadamente a la mitad los bytes de
checkpoints frente a10, con margen temporal en la carga medida. K=50 ahorra
más memoria y aumenta el tiempo de reconstrucción; no se afirma que20 sea
óptimo para cualquier estado. Las tres variantes con checkpoints tuvieron cero
consultas mayores de50 ms; la alternativa sin checkpoints tuvo777/1000.
El máximo de acciones y deltas se instrumenta sobre consultas reales. La memoria
Python se midió en una ejecución complementaria de la misma carga, contando
objetos del bloque serializable y deduplicando referencias con TablaIndice
propia; no incluye el juego vivo externo, la UI ni memoria temporal del índice
de medición. El informe también registra pico temporal de consulta mediante
tracemalloc y tamaño JSON compacto. No confundir bytes JSON con memoria RAM.

Reproducción dirigida equivalente a la sección004 de `--bench`:

```bash
.venv/bin/python -c 'from src.orchestrator.bench_historia import bench_historia; print(bench_historia())'
```

Se conserva además el diagnóstico de diario sintético de una sala y dos eventos
por acción en `docs/mediciones/004-historia-2026-11-10.json`; no sustituye el
resultado del motor real. Sus tamaños parciales JSON iniciales incluyen espacios,
mientras que el tamaño total es compacto; la tabla anterior usa exclusivamente
el informe principal con separadores consistentes.

**Compatibilidad y errores.** Formato v4 con índice de64 bits y bloque histórico
versionado en core. El flujo de juego rechaza v1/v2/v3; lectores técnicos legados
permanecen separados. Carga candidata valida cortes, deltas, checkpoints y su
coherencia antes de instalar. Pruebas de fallos inyectados de captura/cierre,
incluido retroceso, verifican rollback por deltas y estado/ramas/log intactos.
Abrir una puerta ya abierta se trata como éxito sin acción ni avance temporal;
se corrigió la rama previa que apilaba esa apertura vacía.

**UI/UX.** Panel H/Historial con navegación por tiempo/acción, foco, teclado y
ratón, barra de vida, sprites de inventario, secciones y grafo del mapa histórico.
Paleta/fuentes/escala compartidas; tokens de8/24 px para espacio/margen y esquinas rectas, coherentes con el pixel-art.
La geometría histórica se cachea por consulta; controles siguen visibles con
listas largas y scroll. Capturas offline revisadas a1024×800 y640×480; pruebas
a640×480,1024×800,1280×720 y1920×1080. El panel suspende movimiento/viaje y
restablece el temporizador al cerrar sin pasos acumulados.

**Límites.** La medición confirma el umbral solo para la carga publicada; no
certifica estados mayores o cazadores de001. La captura de conocimiento utiliza
una proyección normalizada del mapa actual y su costo debe reevaluarse con mapas
grandes. §5.6 completo conserva su alcance transversal y espera también la carga
nueva de A. El recorrido manual humano de UI sigue pendiente (T033); capturas y
eventos headless no se presentan como esa validación. Regresión final:464
aprobadas/1 omitida (integración HTTP opcional), 14,39 s.

### Corrección visual004 — 2026-11-10

Por instrucción explícita del usuario («remueve las esquinas redondeadas. eso
aquí no se permite»), se eliminan los radios de paneles, botones, campos,
barras y nodos del historial, incluido su acceso desde el juego. La retícula
de8 px se aplica al espaciado y los márgenes; no autoriza esquinas redondeadas.
Se corrigen especificación, plan, tareas, contrato y capturas para mantener la
estética de rectángulos duros ya documentada en la decisión30.

### Tipografía compartida y recuperación tras cierre — 2026-11-10

Se retoma el cambio de presentación que había quedado en el árbol de trabajo.
`src/view/tipografia.py` centraliza Lato con archivos originales Regular400,
Medium500, Semibold600 y Bold700, incluidos en `assets/fonts/` con licencia OFL.
Los roles tienen tamaño mínimo real, interlineado en múltiplos de4 px,
tracking medido y caché de fuentes. Las cifras0–9 tienen ancho uniforme en las
cuatro variantes. La geometría del escenario conserva su escala; la lectura no
se comprime al reducir la ventana. No se modifican contratos ni reglas del motor.

Se integran roles en menús, HUD e historial; se ajustan textos y acciones a
ventanas pequeñas. Controles permite desplazamiento con rueda/flechas/PageUp/
PageDown. Las etiquetas truncadas registran texto completo para tooltip con
ratón o foco/selección; el tooltip envuelve, permite scroll y queda en la ventana.
Se corrige también la envoltura cuando ni la elipsis cabe, evitando un bucle.
El mapa usa respaldo opaco y medidas legibles para separar título/instrucciones.
Los títulos y subtítulos sobre arte tienen respaldo sólido; botones deshabilitados
usan texto legible. Se corrigen el margen del botón Volver a4K, filas del resumen
final y escala de indicadores de dificultad. Se conservan las esquinas rectas.

Validación: `.venv/bin/python -m pytest -q`: **487 aprobadas/1 omitida**
(integración HTTP opcional),6,22 s. `git diff --check` sin errores. Pruebas nuevas
verifican archivos/pesos originales, cifras tabulares, caché, métricas de dibujo,
interlineados, mínimos, parejas de contraste compartidas y tooltip completo con
foco/scroll. Los colores normales compartidos pasan4.5:1 en panel, fondo, hover
y deshabilitado; acción clara y error sobre rojo oscuro también pasan4.5:1.
Estas comprobaciones parciales no equivalen a conformidad WCAG global.

Evidencia visual headless con sprites reales y FakeBackend de `tests/test_vista.py`:
`docs/mediciones/tipografia-640.png`, `tipografia-1024.png` y `tipografia-1280.png`.
Cada mosaico conserva píxeles nativos de640×480,1024×800 o1280×720:
filas inicio/selección, pausa/ajustes, controles/HUD, mapa/historia y fin/error.
Incluyen cinco criptas de nombre largo, historia con40 objetos y nombre extenso,
y error largo con acceso completo. Se revisaron capturas para detectar solapes;
la regresión también verifica límites de controles hasta3840×2160.
No sustituye un recorrido humano interactivo ni cierra T033 de004.

Antes del commit, el usuario solicita mayúscula inicial como mínimo en los
elementos visibles. Se incorpora `texto.inicial_mayuscula` para etiquetas,
objetos, tooltips, avisos y nombres de presentación; se corrigen ayudas,
subtítulos y leyendas del mapa. Se conserva el resto del texto y las siglas,
sin alterar identificadores ni datos del motor. Se regeneran los tres mosaicos.
Regresión final con esta corrección: **494 aprobadas/1 omitida**,6,19 s;
`git diff --check` sin errores.

### Títulos sobre arte sin panel blanco — 2026-11-10

Por corrección explícita del usuario, `_caja_menu` elimina los rectángulos
blancos del título y subtítulo. Ambos se dibujan directamente sobre el arte,
con texto claro y contorno oscuro limitado a los glifos. Cada línea del
subtítulo se centra respecto al mismo eje del título, también cuando envuelve.
La pareja texto claro/contorno oscuro supera4.5:1; no se afirma conformidad
global sobre el arte. Se actualizan los mosaicos de640×480,1024×800 y1280×720
y se revisa la selección a tamaño nativo. Validación dirigida:133 aprobadas/
1 omitida (vista, historial y tipografía),4,57 s; `git diff --check` sin errores.

### Proporción del título al redimensionar — 2026-11-10

Se reemplaza la selección entre dos tamaños fijos del título sobre la caja por
un tamaño proporcional al alto real del arte, calculado en píxeles finales.
El ajuste anterior mantenía demasiado grande el texto pequeño y podía caer a
la fuente de botón en ventanas grandes. El nuevo cálculo aplica la escala una
sola vez, mide el ancho y ajusta gradualmente, con mínimo18 px para este título
compacto y peso600 si es menor de24 px. No cambia los mínimos de texto continuo.
Ejemplo «Elige tu cripta»:19 px a640×480,31 a1024×800,28 a1280×720,
42 a1920×1080 y84 a3840×2160. La escala sigue la caja y su espacio vertical.
Se conservan subtítulo centrado y ausencia de fondos blancos.

Validación dirigida:137 aprobadas/1 omitida (4,63 s). Pruebas de proporción,
crecimiento y encaje de cuatro títulos entre640×480 y4K. Se regeneran los tres
mosaicos y se revisan capturas nativas a640×480 y1920×1080. Revisión headless;
`git diff --check` sin errores.

## Resolubilidad003 — diseño y evidencia estructural,2026-11-16

**Estado:** elección de diseño sustentada en microbenchmarks locales; verificador
completo pendiente de implementación/medición. No se declara aceptación de200 ms.
Plan: [003](specs/003-resolubilidad/plan.md); decisiones D01–D08 y alternativas en
[research.md](specs/003-resolubilidad/research.md). Cada decisión referencia FR-RES.

**Problema y elección (FR-RES-01–07/12):** obtener el cierre incremental de salas
alcanzables y llaves sin repetir búsquedas completas por llave; guardar evidencia
para frontera y ciclos con alternativas. Compartir DatosSala/DatosSalida y el
constructor neutral existente con001/002, ampliándolos con llave/estado inicial
sin un modelo003 paralelo (D01). Reglas monotónicas, contadores y suscriptores por
hecho; cada sala/llave se activa una vez y cada incidencia se procesa un número
constante de veces (D02). Descubrir una sala no dispara sus salidas: primero
se atienden sus llaves y después las salidas N/S/E/O; pendientes se enlazan
al identificarlas, no en orden de compilación. Costos de001 se conservan y no ordenan la verificación.

**Estructuras (D03, FR-RES-05/07/12/13):** cola FIFO propia encapsulada sobre
arreglo+cursor de cabeza; índices propios TablaIndice para IDs→ordinales;
marcas booleanas y contadores por ordinal compacto; adyacencias y pendientes
por enlaces/ordinales; pilas iterativas propias para reducción residual. Para
IDs textuales se amplía TablaIndice neutral con claves str y hash propio
FNV-1a64 sobre bytes UTF8, enmascarando cada paso y comparando igualdad textual
completa para resolver colisiones. Se preservan claves enteras/extremos y el
texto original. La codificación a entero grande fue medida como alternativa
preliminar y se descarta: los desplazamientos de `_hash_entero` no justifican
costo lineal en bytes arbitrarios. El índice textual se mide por separado.
No usar heapq, deque, set/frozenset, dict como índice, sorted ni list.sort en003.
Arreglo+cursor no desplaza elementos; retiene O(n) referencias hasta terminar la
verificación. La cola enlazada es una alternativa válida, descartada por su costo
medido en estas cargas. No se usa orden de cubetas como orden de obtención.

**Medición efectivamente ejecutada:**
[script](docs/mediciones/003-estructuras-plan.py) y
[muestras/entorno](docs/mediciones/003-estructuras-plan.json), Python3.12.3,
Linuxx86_64, semilla300316, dos calentamientos, siete repeticiones,
perf_counter_ns y checksums iguales entre alternativas. Se mide construcción y
consumo/consulta; la variante textual incluye conversión, construcción y consulta.

| Alternativa | Entradas | Mediana ms | Máximo ms |
|---|---:|---:|---:|
| fifo_lista_cabeza | 32000 | 2.995 | 3.470 |
| fifo_pop_cero | 32000 | 83.017 | 85.421 |
| fifo_enlazada | 32000 | 9.459 | 15.423 |
| indice_propio_entero | 4000 | 19.806 | 21.235 |
| busqueda_lineal | 4000 | 174.224 | 187.317 |
| indice_propio_texto_codificado | 4000 | 46.665 | 53.876 |
| indice_propio_texto_fnv1a64 | 4000 | 47.769 | 54.755 |
| busqueda_lineal_texto | 4000 | 169.080 | 184.690 |
| indice_propio_texto_codificado_largo | 4000 | 392.360 | 403.575 |
| indice_propio_texto_fnv1a64_largo | 4000 | 535.167 | 545.149 |

El arreglo+cursor y el índice propio evitan el crecimiento observado al quitar
frentes y buscar IDs repetidamente. Marcas densas por ordinal se miden por
separado en el JSON; no se dimensionan por max(id). IDs textuales medidos de16
caracteres ASCII: no se infiere costo constante para longitudes ilimitadas.
La tabla tiene costo esperado amortizado, no peor caso garantizado frente a
colisiones adversarias. Medir cadenas/colisiones y bytes de IDs en el benchmark
completo. Estas cifras no miden propagación, diagnóstico de ciclos ni red/vista.

**Ciclos (D04/D05, FR-RES-05/06/07/12/15):** se conserva evidencia AND/OR y se
reduce globalmente con Tarjan iterativo sobre el residuo compilado, sin
recorridos nuevos del esqueleto por llave. Primero elegir llave de un circuito
por orden de consulta y luego primer retorno con dependencias en orden fuente.
A por B O C, B y C por A muestra por qué un circuito no equivale a dependencia
individual inevitable: el usuario autorizó «pues hazlo» para presentar una
alternativa circular y las demás alternativas bloqueadas. Ajustados FR-RES-07/15
y escenario13. El costo de reducción cuenta dentro de200 ms. No se sostiene que
componentes conexas por sí solas demuestren requisitos inevitables.

**Alternativas descartadas:** búsquedas O(K(S+E)) por llave, solo como referencia
lenta de laboratorio; grafo con todas las parejas de llaves por camino, por
explosión y pérdida de alternativas; menor id global, por contradecir el
orden de descubrimiento aprobado. El costo total previsto es esperado
O(S+E+K+L+B+R) y memoria lineal, contando ubicaciones, bytes e informe emitido.

**Integraciones (D06/D07, FR-RES-08–11/14/15):** `/criptas/{id}/llaves` con mismo
budget, cache de id/versión y offline; preparación antes de crear juego,
`--verificar` sin vista, forzado solo para negativo demostrado y reporte textual
común. Propuestas reviewables en contracts/, sin modificar CONTRATOS.md ni
atribuir aprobación a compañeros. No cambia guardado v4/replay; errores de carga
no se fuerzan. Los auxiliares de003 no pueden reutilizar set heredados de otros
subsistemas; auditar tránsito del flujo puro/preparador sin declarar todo el
repositorio conforme.

**Criterio de aceptación D08 (FR-RES-01–15):** `--bench` con familias por semilla,
cadenas largas y ciclos; comparar contra búsqueda repetida con datos idénticos,
contadores y muestras completas, no solo mejor tiempo. Mayor cripta publicada:
100 verificaciones completas con máximo≤200 ms, incluidos resumen/texto y
preparación local, excluyendo red/render. T043 y T044 ya están medidas y sus
artefactos se detallan abajo; las sintéticas no sustituyen la carga publicada.
Pruebas funcionales/CLI y regresión001/002/004 pasan. La revisión visual
headless está hecha; solo queda el recorrido humano de T045. El plan no modifica
producción.

Nota de medición003: el hash textual FNV no gana en tiempo a la codificación
entera en estas muestras; se elige por su costo lineal por byte y acumulador
acotado. Con4000 IDs de256 caracteres supera200 ms el microbenchmark del
índice: no se garantiza200 ms para entradas arbitrarias ni se atribuye esa
cifra al verificador; la aceptación exige la mayor cripta publicada real.

### Cierre de implementación003 — 2026-11-16

Implementación y validación registradas en
[quickstart](specs/003-resolubilidad/quickstart.md). Suite final:
`.venv/bin/python -m pytest tests/ -q` → **573 passed, 1 skipped**. La auditoría
AST de003 pasa; `git diff --check` sin errores. Se conserva explícita la desviación de orden:
T009–T018 pasan ahora, pero no se registró su fallo antes de T019–T027.

`docs/mediciones/003-resolubilidad-sinteticas.json` guarda20 casos, semilla300316,
dos calentamientos y siete muestras por caso, Python3.12.3, Linux y
Intel Core i7-1185G7@3.00GHz. En K≈8193, cadena: mediana165.27 ms/máximo191.03;
ciclo:245.63/264.22; alternativas:152.79/158.32; desconexión:151.37/159.92.
La familia de puertas pendientes usa S8195/E32772/K8194 y dio348.49/417.24 ms.
El reporte de ciclo mide1,187,078 bytes; cada familia grande registró2151
colisiones de cubeta de IDs y un máximo de5 entradas por cubeta. No se concluye
el límite de200 ms de la cripta oficial con datos sintéticos.

T044 queda satisfecha con la cripta mayor publicada (`cripta-06`,300 salas,
versión `f9ed9afa683d`). La API devuelve cuatro ubicaciones en la forma legada
`{"llaves":[...]}`; el adaptador solo admite esa forma exacta en el endpoint no
paginado y aporta ID/versión desde la ficha validada. El DTO versionado estricto
sigue vigente para las demás formas. Cien verificaciones completas dieron
paquete crudo de96,801 bytes; mediana1.504 ms y máximo7.660 ms (≤200 ms);
muestras y entorno están en
`docs/mediciones/003-resolubilidad-publicada.json`, paquete crudo en
`docs/mediciones/003-reporte/003-resolubilidad-publicada-paquete.json`.
`.venv/bin/python -m src.main --bench` terminó con código0 e incluyó las
mediciones sintéticas de003 en su salida; debido a que ejecuta también los
benchmarks históricos, tardó unos seis minutos.
T045: se regeneraron y revisaron headless menú, selección, nombre largo con
tooltip, reporte largo/error/scroll, HUD, mapa e historial a640×480,1024×800 y
1280×720. El texto del reporte sobre panel contrasta13.57:1, título6.92:1 y
texto claro sobre acción6.81:1. Falta el recorrido humano; no se equipara al
headless ni se afirma conformidad WCAG global.
La inspección visual estática de las 27 capturas detectó y corrigió solapamiento
del badge con “Salas” en tarjeta compacta a640×480; test de geometría nuevo y
capturas regeneradas. T045 permanece abierta solo para recorrido interactivo
humano.

Al revisar la integración remota de001, `origin/main` estaba en el mismo
`b81b1af` que HEAD. La especificación `specs/001-terreno-cazador/spec.md` está en
Draft y solo tiene checklist; no hay plan/tareas ni implementación del
comportamiento cazador en `src/`. La base ya contiene `DatosSalida.costo`, Dijkstra
genérico, reloj con costo parametrizable y muestra de costos en el mapa, pero
`Exit` no parseaba costo y C2 seguía agendando movimiento/enemigos con costos
fijos. Este cambio añade `Exit.costo` default100 y lo proyecta en el modelo
compartido, conectando una parte de la base con003/001. Cazador/rango, decisión
ponderada, actualización ante puertas, movimiento y benchmark CAZ continúan
pendientes. La compatibilidad existente se comprobó con la regresión completa.

## 2026-11-16 — Convergencia 001: tipos y comparador

Se conserva el contrato estricto compartido con 003: costo omitido vale100; null, booleanos y texto se rechazan. La prueba001 esperaba ValueError para texto y aceptaba null, contradiciendo validación y pruebas del esqueleto. Se corrige la expectativa y se elimina normalización muerta en Exit.from_dict. El comparador de laboratorio usa nodos enlazados (valor,siguiente) en lugar de extracción frontal de arreglo; conserva inserción O(V), frente a O(log V) del montículo. Una regresión compara costos y poda entre ambos.

Validación inicial completa:591 pasan,1 omitida y1 fallo de rendimiento (37,9ms en prueba de decisiones, pendiente T047). No se declara cierre de001.

001 T045: la búsqueda ordinaria comienza en el cazador y poda antes de insertar fuera del rango. Las etiquetas (costo,primer_vecino) se propagan por montículo ordenado por etiqueta/ID, descartando entradas obsoletas. Se conserva cálculo inverso para comparaciones explícitas. La regresión con jugador distante falló primero (exploraba1,2,3) y verifica ahora exclusivamente la región997–1000.
