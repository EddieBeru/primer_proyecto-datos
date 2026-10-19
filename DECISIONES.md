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
    `sfx.VOLUMEN = 0.25` aplicado con `set_volume` al cargar el jingle (0.5 seguía fuerte: pygame mide amplitud lineal). `sprites.py` clasifica por palabras clave (`_CLAVES_POCION`, `_ARMA`, `_ARMADURA`, ...): poción de velocidad/antídoto reutilizan `pocion-salud.png`, protección (coraza, peto...) usa `escudo.png`, armas (mandoble, daga...) usan `espada.png`, `llamas-01` dejó de salir magenta (trampa). Se corrigió un "espada" duplicado en las claves.
    Descartado: un PNG por id (imposible con el catálogo abierto de la API) y colores de respaldo por hash (el usuario pedía arte real por familia).
63. **Retroceso real por intervalos: el tope 5 cuenta acciones del jugador, no eventos (+ un solo marcador de turno).**
    El tope contaba ENTRADAS: cada pulso de veneno, rearme o turno gastaba cupo, así que un intervalo largo podía expulsar la acción del jugador de la ventana y `deshacer` moría con "Nada que deshacer." (o revertía eventos sueltos sin su acción). Ahora `PilaDeshacer` cuenta intervalos: cada acción de `ACCIONES_JUGADOR` (mover, abrir, esperar, daño, recoger, soltar, equipar, pociones…) abre uno — "trampa" no: pertenece al intervalo en que se pisó; al superar `TOPE=5`, `_olvidar_mas_vieja()` corta en la 5.ª frontera y descarta la acción más vieja CON todo su intervalo. Cada frontera guarda reloj/acciones/rastro de antes y el bloque común de `aplicar_inversa` los restaura; los inversos devuelven los turnos consumidos (`turno_antes` reinsertado con su `(t, seq)`), `derrotados_antes`, los contadores de veneno/quemadura, sala/rastro/visita (durmiendo lo despertado y cancelando TODOS sus turnos pendientes, no solo el de activación) y la oleada (`oleada_antes` + cancelación de la reprogramada). `Agenda.reinsertar(t, tipo, datos, seq)` conserva `(t, seq)` sin tocar el contador interno. De paso se corrigió la cadencia del reloj (§2.3): el marcador del jugador se acumulaba y `_programar_turno_jugador` ahora garantiza A LO SUMO un marcador pendiente (cancela los anteriores; con save, `inicial=True` respeta el cargado), y `Fachada.deshacer` reinserta el suyo en el instante rebobinado con seq `-1` para que el drenaje lo consuma primero en empates y el estado quede congelado justo ahí. Deshacer no consume azar ni reescribe la pila: la paridad del replay se mantiene.
    Descartado: subir el tope (seguiría desalojando la acción), etiquetar cada entrada con su acción (mismo corte, más contabilidad) y rebobinar el azar (no lo consume el retroceso).
    Pruebas: `test_pila_tope_por_intervalos_descarta_solo_el_mas_viejo`, `test_agenda_reinsertar_conserva_t_y_seq`, `test_deshacer_sin_accion_no_consume_pergamino`, `test_deshacer_esperar_es_accion_y_restaura_reloj`, `test_deshacer_devuelve_sala_y_restaura_intervalo`, `test_pergamino_devuelve_a_la_sala_anterior` y la de aceptación `test_seis_acciones_deshacer_cinco_vuelve_al_estado_de_la_primera` (6 acciones, 5 retrocesos y el retrato observable queda idéntico al de una sesión que solo jugó la 1.ª). `test_oleada_deshacer_la_retira` y `test_deshacer_regeneracion_corta_pulsos` se adaptaron (abren intervalo con `esperar`).
64. **El pergamino se ve: rebobinado violeta y el prota reaparece junto a la puerta.**
    El retroceso ya redibujaba todo (§7) pero el cambio de sala era un salto seco. `capas.dibujar_rebobina(sup, area, fase)` pinta 18 frames (`app.REBOBINA_FRAMES`) de anillos violeta (`paleta.MAGIA`) que se expanden hacia afuera con velo y chispas girando al revés sobre la caja de la sala; es determinista (sin azar), se recorta al arte (el HUD queda legible) y `VistaApp.enviar` lo dispara SOLO si `deshacer` fue aceptado (los rechazos no destellan), apagándose solo en `dibujar()`. Si el retroceso cambió de sala, `_aparecer_tras_retroceso(sala_antes)` busca la puerta de la sala actual cuyo destino es la abandonada y planta al prota de ese lado del vano (`JUNTO_A_PUERTA`, con `OPUESTA` que ahora comparte `_revisar_puerta`), con `en_puerta=True` para no recruzar por proximidad y la animación de paso en cero; retrocesos dentro de la misma sala conservan la posición.
    Descartado: fantasma del prota saliendo de la sala (no se guarda la posición previa; el anillo + velo ya leen "rebobina"), sonido sintético (sin asset y la vista no usa numpy) y destello también en los rechazos.
    Pruebas: `test_rebobina_anillos_violeta_y_apagado` (pinta en violeta, fase 0 no pinta, misma fase = mismos píxeles) y `test_deshacer_rebobina_y_reaparece_en_la_puerta` (dispara solo al aceptar, posición junto a la puerta, expira solo); fotogramas renderizados a mano (`rebobina_*.png`).
