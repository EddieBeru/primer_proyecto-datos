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

10. **Daño con randint(0,4) y Random(semilla).** Doc §2.6 lo exige + reproducibilidad. Descartado: determinista sin azar (no coincide observable).
11. **Intervalo por costo (`costo*100//vel`) + reescale.** Doc §2.3 + tabla costos. Descartado: `base//vel` único (mover≠recoger).
12. **Rastro timestamp + fresco <400, empate menor id.** Doc §2.9/§4.7. Descartado: intensidad con decaimiento (otra semántica).
13. **Errante con azar, rastreador solo vecinas abiertas.** Doc §2.8. Descartado: hash determinista sin RNG.
14. **Abrir(50)≠mover(100), llave no consume.** Doc §2.5. Descartado: auto-abrir al mover.
15. **Veneno 80x5=400, rearme 300 default, regen 200 capada.** Doc §2.10. Descartado: ticks genéricos.
16. **Victoria con puerta abierta, tabla sin fórmula.** Doc §2.12. Descartado: puntaje `salas*100...` y victoria con llave en bolsillo.
17. **Pergamino por intervalo + exclusión + tope 5, sin copias.** Doc §2.11/§4.6. Descartado: una entrada por evento (revierte de a uno).
18. **Bitácora header + validación, pantalla 20 circular.** Doc §4.11/§4.8. Descartado: sin header y `mensajes[-50:]`.
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
