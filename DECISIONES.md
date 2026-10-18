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
