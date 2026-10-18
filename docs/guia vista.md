# Guía completa para la Vista — cómo conectarse al orquestador

Para quien programa la interfaz (consola o Pygame). Todo lo que la vista
necesita —y lo que tiene prohibido— está aquí. Si algo no está en este
documento, se pide por contrato (regla 6.3), no se calcula en la vista.

Complementa a `vista y flujos api.md` (qué dibujar) y
`separacion vista controlador.md` (quién hace qué). Este documento es el
manual operativo: clases, llamadas, datos exactos y ejemplos.

---

## 0. La regla de oro (leer primero)

```
VISTA  →  solo habla con Sesion (src/orchestrator/sesion.py)
           solo envía INTENCIONES (strings) y lee FOTOS (FotoEstado)
           NUNCA toca EstadoPartida, Agenda, budget, endpoints, archivos
```

- La vista **no decide reglas**: no calcula daño, no mueve enemigos, no abre
  puertas por su cuenta, no descuenta presupuesto, no inventa contenido.
- La vista **no llama a C1 ni al API**: nada de `src.controller1`, `RoomLoader`,
  `CacheLRU`, `savegame` directo. Todo pasa por `Sesion`.
- Si falta un dato en la foto, no lo derives: pide ampliación de K5.
- Referencia viva de este contrato: `src/orchestrator/consola.py` (consola oficial).
  Si la consola puede jugar la partida completa solo con `Sesion`, tu vista
  también puede. Úsala como ejemplo de integración mínima.

---

## 1. Conexión en 10 líneas

```python
from src.orchestrator.sesion import Sesion

# 1. Crear sesión (elige backend UNA vez; ver §2)
ses = Sesion(backend=None,       # None = API real; ver §2 para offline/falso
             cache_size=25,       # tope caché catálogo (§4.4)
             jugador="ana",       # nombre para tabla de puntajes
             log_ruta="partida.log",        # bitácora replay (recomendado)
             puntajes_ruta="puntajes.jsonl")

# 2. Iniciar partida (devuelve la primera foto)
foto = ses.iniciar("cripta-01", semilla=7)

# 3. Bucle de juego: intención -> foto -> dibujar
ok, msg, foto = ses.paso("n")    # moverse al norte
dibujar(foto)                    # tu render con la foto (§3)
if not ok:
    mostrar_error(msg)           # error amable, la partida SIGUE (§6)

# 4. Al terminar (foto.estado != "jugando")
resultado = ses.finalizar()      # registra puntaje + reporte red (§9)
```

`Sesion` también se construye con `log_ruta=None` (sin archivo) pero entonces
no hay `--replay` de esa partida: **siempre pasa `log_ruta` en juego real**.

---

## 2. Backends: real, offline y falso

El backend se elige **una vez** al crear la `Sesion`. La vista no lo toca
después; solo lo pasa al constructor (normalmente desde `main.py --offline`).

| Backend | Cuándo | Cómo |
|---|---|---|
| API real | Juego normal | `Sesion(backend=None)` (usa `src.controller1.endpoints`) |
| Offline | Sin internet / evaluación | `Sesion(backend=OfflineBackend("paquete/"))` — lee disco, **no gasta presupuesto** |
| Falso | Tests / desarrollo sin red | Backend propio estilo `tests/test_sesion.py::FakeBackend` (6 salas fijas) |

Protocolo que todo backend cumple (por si haces uno): `info_cripta`,
`version_cripta`, `version_catalogo`, `esqueleto_completo`, `contenido`,
`lote_catalogo_auto`. Test de conformidad:
`tests/test_sesion.py::test_backends_cumplen_protocolo`.

---

## 3. La foto: `FotoEstado` campo por campo

`ses.foto()` y cada `ses.paso()` devuelven una `FotoEstado`
(`src/controller2/fachada.py`). Es **solo lectura**: dibújala, no la mutes
(mutarla no cambia la partida y rompe tu próximo render).

| Campo | Tipo | Contenido exacto | Úsalo para |
|---|---|---|---|
| `sala_id` | `int` | id sala actual | Título "Sala N: nombre" |
| `sala_nombre` | `str` | nombre (`"?"` si desconocida) | Título |
| `puertas` | `dict[D, {...}]` | `D` ∈ N/S/E/O. Valor: `{"destino": int, "cerrada": bool, "llave": str\|None}` | Capa fondo: dibuja puerta por dirección; `cerrada`+`llave` → icono candado |
| `objetos_suelo` | `list[str]` | ids de catálogo en el suelo | Capa estática (iconos por id) |
| `trampas` | `list[{instancia, tipo, armada}]` | trampas de la sala; `armada: bool` | Capa estática: armada vs desactivada |
| `jugador` | `dict` | `vida, vida_max, ataque, defensa, velocidad, efectos: dict` | Barras + stats + indicadores |
| `enemigos` | `list[{instancia, tipo, comportamiento, vida}]` | `comportamiento` ∈ guardián/errante/rastreador; `vida` = vida actual (máx. en catálogo si lo necesitas… no lo tienes: ver §8) | Capa actores + barra de vida + color por comportamiento |
| `inventario` | `list[str]` | ids **en orden real**; `[0]` = equipado al frente | UI inventario en orden |
| `equipado` | `str\|None` | `inventario[0]` o `None` | Resaltado |
| `pergaminos` | `int` | nº de pergaminos de retroceso | UI deshacer ("U (n)") |
| `mensajes` | `list[str]` | últimas ≤20 líneas `"reloj\|tipo\|actor\|detalle"` | Panel de mensajes (tal cual, o parseadas) |
| `presupuesto` | `int` | solicitudes restantes | **Solo modo desarrollo** (no mostrar al jugador normal) |
| `estado` | `str` | `"jugando"` / `"victoria"` / `"derrota"` | Cambio de pantalla (§9) |
| `error` | `str\|None` | último error amable, o `None` si la última intención fue ok | Pantalla 1.6 / toast |
| `en_pausa` | `bool` | siempre `False` hoy (pausa la gestiona tu menú) | Reservado |

Detalles que importan al dibujar:

- **`jugador.efectos`**: dict `{nombre: restante}`. Claves posibles:
  `veneno` (ticks restantes), `veloz` (turnos con velocidad subida),
  `antorcha` (luz restante). Vacío = sin efectos. Muestra un indicador por
  clave con su número.
- **`puertas`**: solo trae las salidas que **existen**. Dirección ausente =
  no hay camino (dibuja muro, no puerta). `cerrada=True, llave=None` =
  trabada (no se puede abrir). `cerrada=True, llave="X"` = pide llave X.
- **`enemigos[].vida`** es vida actual. No trae `vida_max` (K5 no lo incluye;
  si lo necesitas para barras proporcionales, pide ampliación K5).
- **`mensajes`**: líneas de bitácora en crudo. Para panel simple, muestra las
  últimas 4–5 tal cual. Formato: `reloj|tipo|actor|detalle`.
- **`inventario` son ids** (`"espada-hierro-01"`), no nombres. Para mostrar
  nombre/icono necesitas resolver el id → ficha. La Sesión **no expone**
  catálogo (decisión K5: la vista dibuja por id con sprite genérico si no lo
  conoce). Opciones: (a) sprite de reemplazo por id desconocido (recomendado,
  igual que el gestor de sprites §7), (b) pedir ampliación K5 con
  `nombres: {id: nombre}` en la foto.

---

## 4. Mandar órdenes: tabla de intenciones

Una intención = un string a `ses.paso(texto)` → retorna `(ok, msg, foto)`.
`ok=True` = se ejecutó (y ya se drenó la agenda, §5). `ok=False` = rechazada
**sin consumir tiempo ni romper la partida**: muestra `msg`/`foto.error` y
sigue pidiendo.

| Texto | Acción | Costo virtual | Notas |
|---|---|---|---|
| `n` / `s` / `e` / `o` | Moverse N/S/E/O | 100 | Exige puerta **abierta**; si cerrada, primero `abrir` |
| `abrir N` | Abrir puerta con llave | 50 | La llave **no se consume**; sin llave = rechazo sin tiempo |
| `atacar <instancia>` | Atacar enemigo | 100 | `instancia` de `foto.enemigos[].instancia`, ej. `atacar e-201` |
| `esperar` | Pasar | 100 | Deja actuar a enemigos/efectos |
| `recoger <id>` | Recoger del suelo | 25 | `id` de `foto.objetos_suelo`; llena = rechazo sin tiempo |
| `usar <id>` | Usar poción/antídoto/antorcha | 50 | Según clase; se **consume** (antídoto cancela veneno) |
| `soltar <pos\|id>` | Soltar al suelo | 25 | `soltar 2` o `soltar pocion-roja-01` |
| `equipar <pos\|id>` | Equipar (va al frente) | 50 | Máx. 1 arma + 1 armadura; la anterior queda en inventario |
| `deshacer` | Pergamino retroceso | 0 (no consume tiempo) | Consume 1 pergamino; revierte intervalo completo (§7) |

Reglas de oro al mandar:

1. **Abrir y mover son dos pasos** (`abrir N` y luego `n`). Si mandas `n`
   con puerta cerrada recibes `ok=False, "Puerta cerrada. Ábrela con X."`.
2. **Atacar usa `instancia`, no `tipo`**: con dos ratas iguales, cada una
   tiene su `instancia` (`e-201` vs `e-202`). Mostrarlas como
   "Rata gigante #1/#2" es válido (§2.6).
3. **`usar` es genérico**: no distingas poción/antídoto/antorcha en tu UI si
   no quieres; la Sesión lo resuelve por clase. (Botón "usar objeto".)
4. **Equipar por id está permitido** (`equipar espada-hierro-01`); la Sesión
   resuelve la posición. Por posición (`equipar 2`) también vale.
5. Tras **cada** `paso()` exitoso la Sesión drena agenda (§5) y te devuelve la
   foto ya actualizada: dibuja siempre la foto retornada, no la anterior.

---

## 5. El loop oficial (tu game loop)

Después de cada intención exitosa, la Sesión ejecuta eventos pendientes
(turnos enemigos, veneno, rearmes, cierres, fines de efecto) hasta el próximo
turno del jugador o fin de partida (§2.3). **No necesitas ni debes llamar a
nada para eso**: `paso()` ya lo hace (tope 500 eventos; si se supera, la
partida sigue y verás el aviso en `foto.error`).

```python
foto = ses.iniciar(cripta_id, semilla)
while foto.estado == "jugando":
    dibujar(foto)
    texto = leer_teclado()          # tu mapeo tecla->intención (§10)
    ok, msg, foto = ses.paso(texto)
    if not ok:
        mostrar_error(msg)          # y vuelve a pedir (sin redibujar todo si no quieres)
dibujar_pantalla_fin(foto)          # victoria / derrota (§9)
resultado = ses.finalizar()
```

- **60 FPS sin problema**: `paso()` es síncrono y rápido (<20 ms sin red,
  §5.2); la única espera real es red (primera entrada a sala no cacheada,
  ~400 ms) y reintentos 429. Muestra "cargando…" si `paso()` tarda: la
  **espera real nunca mueve el reloj virtual**, así que puedes bloquear el
  input con spinner sin romper determinismo.
- **No llames `paso()` en segundo plano ni en hilos**: una intención por vez,
  siempre con la última foto.
- **Pygame**: el `esperar_fn` de reintentos 429 hoy bloquea (`time.sleep`).
  Si quieres "esperando N s…" sin congelar la ventana, pide hook no-bloqueante
  (trabajo pendiente documentado, no implementado).

Mapeo de teclado sugerido (§10.2 + Parte 1 §5 del doc de vista):

| Tecla | Intención |
|---|---|
| W/↑, S/↓, D/→, A/← | `n`, `s`, `e`, `o` |
| E (sobre puerta) | `abrir <dir>` (la dir que mira el jugador) |
| Espacio / clic enemigo | `atacar <instancia>` (selección previa si hay varios) |
| F / clic objeto | `recoger <id>` |
| Q | `soltar` (el seleccionado) |
| Tab | recorrer inventario (solo tu UI, no manda nada) |
| Enter sobre objeto | `equipar` o `usar` según clase (si no sabes la clase: botón "usar" para todo lo usable y "equipar" para equipo; o dos botones) |
| U | `deshacer` |
| Esc | tu menú de pausa (§9), no es intención |

---

## 6. Errores: qué mostrar y cuándo

`ok=False` nunca es crash. Patrones:

| Situación | `ok, msg` | `foto.error` | Tu UI |
|---|---|---|---|
| Dirección sin salida | `False, "No hay camino por ahí."` | set | Toast + no redibujar |
| Puerta cerrada | `False, "Puerta cerrada. Ábrela con X."` | set | Toast + resaltar puerta |
| Abrir sin llave | `False, "Necesitas la llave X."` | set | Toast (sin costo: puede reintentar gratis) |
| Inventario lleno | `False, "Mochila llena (N)."` | set | Toast + abrir inventario |
| Enemigo ausente/muerto | `False, "Ese enemigo no está aquí."` | set | Refrescar lista |
| Sin pergaminos | `False, "Sin pergaminos."` | set | Deshabilita botón U |
| Servidor ocupado | `False, "No se pudo entrar a la sala: ..."` | set | Pantalla 1.6 + reintentar |
| Presupuesto agotado | `False, "No se pudo entrar... "` | set | Pantalla 1.6 (partida sigue con lo cargado) |
| Comando desconocido | `False, "¿...? (ayuda: ...)"` | set | Ayuda |

Regla: si `ok=True`, `foto.error` es `None`. Si `ok=False`, el estado del
juego **no cambió** (los rechazos no consumen tiempo: reintentar es gratis).

---

## 7. Deshacer (pergamino): qué ve el jugador

- `foto.pergaminos` = disponibles. `deshacer` consume 1 y revierte **todo el
  intervalo**: la última acción del jugador + lo ocurrido después (ataques
  enemigos, veneno, reloj, puertas, trampas, rastro). No es "volver a la sala
  anterior".
- Máximo 5 intervalos atrás (pila con tope; lo más viejo se olvida).
- `usar pergamino` no consume tiempo: dos `deshacer` seguidos retroceden dos
  acciones.
- Tu UI: botón U con contador (`pergaminos`); deshabilitado en 0; tras
  `deshacer` redibuja **todo** (sala, vida, inventario y mensajes cambian).

---

## 8. Sprites y datos visuales

- **9 clases** (`tipo` en catálogo; en foto solo ves ids): `enemigo`, `arma`,
  `armadura`, `pocion`, `antidoto`, `llave`, `antorcha`,
  `pergamino_retroceso`, `trampa`. Un dibujante único por id + **sprite de
  reemplazo** para ids no previstos (el catálogo lo define el profe).
- **Comportamientos** (`enemigos[].comportamiento`): `guardián` (quieto),
  `errante` (vagabundo), `rastreador` (cazador). Distingue color/icono.
- **Puertas** (4 dir × estado): inexistente / abierta / cerrada-con-llave /
  trabada. `cierre_automatico` no se expone: la puerta simplemente se cierra
  sola en algún paso posterior (verás `cerrada=True` de golpe: normal).
- **Efectos** (`jugador.efectos`): `veneno`, `veloz`, `antorcha` + restante.
- **Vida enemiga**: `vida` actual sin máximo en foto. Barra proporcional al
  máximo no es posible hoy; alternativas: barra normalizada al primer valor
  visto (se resetea por partida) o pedir ampliación K5.

---

## 9. Pausa, guardado, fin, puntajes

```python
# Pausa (tu menú, Esc): la Sesión solo congela lógica vía no-llamar-paso.
ses.guardar("partida.bin")            # binario v2 + "partida.bin.cache"
foto = ses.cargar("partida.bin")      # valida versiones; mismatch = excepción
foto = ses.cargar_en_frio("partida.bin")  # resume sin iniciar antes
```

- `cargar` puede lanzar `GuardadoError` (archivo dañado, versión de formato
  desconocida, **versión de cripta/catálogo incompatible**): muéstralo como
  pantalla 1.7 "versión anterior", nunca cargues a medias.
- Fin: `foto.estado` es `"victoria"` (entró a salida con su puerta abierta)
  o `"derrota"` (vida 0). Llama `ses.finalizar()` **una vez**:
  ```python
  {"terminada": True, "estado": "victoria",
   "puntajes_ruta": "puntajes.jsonl",
   "red": {"realizadas": N, "presupuesto": P, "restantes": R, "hits": H, "misses": M}}
  ```
  Si aún jugando: `{"terminada": False, ...}`. El dict `red` sirve para tu
  pantalla de estadísticas y el informe.
- `mensajes` de fin: las líneas `victoria`/`derrota` ya vienen anotadas.

---

## 10. Replay, bench y modos sin vista

- **Replay**: cada partida con `log_ruta` genera `partida.log` (header
  `#cripta <id> <ver> <vercat> <semilla>` + líneas). `ses.reproducir(log)`
  valida y re-ejecuta sin interacción; mismatch de versiones = excepción
  (no reproduce a medias). CLI: `python -m src.main --replay partida.log
  [--offline paquete/]`.
- **Bench**: `python -m src.main --bench` (sin vista ni red).
- **Offline**: `Sesion(backend=OfflineBackend(dir))` o `--offline`; no gasta
  presupuesto. Ideal para probar tu vista sin red.
- **Jugar ya**: `python -m src.main --jugar [--offline DIR] [--semilla N]`
  abre la consola oficial sobre Sesión — pruébala antes de programar la tuya.

---

## 11. Ejemplo completo (consola como especificación ejecutable)

```python
from tests.test_sesion import FakeBackend  # cripto de 6 salas sin red
from src.orchestrator.sesion import Sesion

ses = Sesion(backend=FakeBackend(), log_ruta="p.log")
foto = ses.iniciar("cripta-ejemplo", semilla=5)
for cmd in ["s", "recoger llave-hierro-01", "e", "abrir N", "n",
            "abrir S", "s", "s", "o", "recoger llave-salida-01",
            "abrir E", "e"]:
    ok, msg, foto = ses.paso(cmd)
    assert ok, (cmd, msg)
assert foto.estado == "victoria"
print(ses.finalizar())
```

Tu vista debe poder replicar exactamente esta secuencia con botones/teclas
(recoger→equipar/usar→abrir→mover→atacar→deshacer) y llegar al mismo final.

---

## 12. Checklist "vista lista" y errores típicos

- [ ] Solo importas `src.orchestrator.sesion` (+ `OfflineBackend` para probar). Nada
      de `src.controller1`, `RoomLoader`, `savegame`, `EstadoPartida` en tu código.
- [ ] Cada frame se dibuja desde la última `FotoEstado`; nunca guardas
      referencia mutable ni la modificas.
- [ ] `abrir` antes de `mover` en puertas cerradas; atacar por `instancia`.
- [ ] `ok=False` → toast con `msg`, sin asumir cambios.
- [ ] Pantallas: juego / victoria / derrota / error amable / versión
      incompatible / pausa con guardar-cargar-salir.
- [ ] `log_ruta` siempre puesto en juego real; `finalizar()` al terminar.
- [ ] Sprite de reemplazo para ids desconocidos; 20 mensajes máx. en panel
      (la foto ya viene topada).

Típicos: usar `tipo` en vez de `instancia` al atacar · asumir que `mover`
abre puertas · dibujar `presupuesto` al jugador · calcular daño/vida en la
vista · llamar `paso()` dos veces por frame · no llamar `finalizar()` y
perder el puntaje.

---

## 13. Anexo 17/10/2026: oscuridad, trampas al caminar y aviso de daño

Tres ampliaciones recientes. Todo sale de la misma `FotoEstado`; la vista no
calcula nada nuevo.

**Sala oscura.** `foto.sala_oscura` (bool) indica que la sala está a oscuras
(el campo `oscura`/`oscuridad` viene de la cripta/API). Sin luz, dibuja un
velo negro sobre el área de sala con un halo alrededor del jugador (así el
resto —HUD, panel de mensajes— queda legible). Con el efecto
`foto.jugador["efectos"]["antorcha"] > 0` la sala se ve completa. Enciende la
antorcha con `usar <id>` (la duración sale de la ficha). Al entrar, avisa
«Sala oscura: usa una antorcha».

**Trampas al caminar.** El motor ya dispara TODAS las trampas armadas al
entrar a la sala (§2.10; siéntelo desde la foto: `trampas[i]["armada"]`).
Dentro de la sala, cuando tu personaje pase a ≤ ~24 px del puesto de una
trampa `armada`, manda `pisar <instancia>` (verás el puesto con el mismo
scatter que los objetos). Respeta el resultado: si `ok` trae un mensaje con
«Ya estaba desarmada» no pasó nada; la foto siguiente te dice si sigue
`armada`. No repitas el disparo mientras sigas encima (espera a salir del
radio) ni lo hagas con trampas desarmadas.

**Aviso de daño.** Tras cada `paso`, si `foto.jugador["vida"]` bajó, muestra
feedback claro (destello rojo + toast). El mensaje de `pisar` ya describe el
daño y el efecto (veneno: pulsos cada 80 durante 400, lo corta el antídoto;
quemadura: pulsos propios que el antídoto no cura). `deshacer` también
devuelve la vida y los efectos.

**Daño y ataque (18/10/2026).** Además del destello, al perder vida el sprite
se tiñe de rojo y tiembla unos frames; al atacar, el personaje siempre
embiste hacia donde mira (con o sin arma) y, si hay arma equipada, además
aparece una estela de espadazo (`capas.dibujar_tajo`). Es dibujo local del
App (misma `FotoEstado` de siempre): no cambia la partida ni añade datos al
contrato K5.

**Espejo y equipo (18/10/2026).** El volteo horizontal es estado propio de la
vista: caminar al Oeste espeja el sprite y al subir/bajar el volteo se
conserva (`app.espejo`), sin volver "de la nada" a la derecha; el
desplazamiento del paso se interpola (`paso_push`) para no brincar de eje.
El arma y el escudo acompañan ese estado: `sprites.escudo(espejo)` y
`sprites.espada(facing, espejo)` rotan/voltean por lado (no por facing crudo)
y `capas.dibujar_actores` los corre a `OFFSET_ESCUDO_LADO`/`OFFSET_ESPADA_LADO`
del lado del espejo. `espejo=None` sigue derivando de `facing=="O"` para
llamadas viejas. Sin cambios de contrato.

**Sonido (18/10/2026).** `src/view/sfx.py` reproduce el jingle de inicio
(`assets/sfx/little_caesars_pizza.mp3`, guiño a la empresa que inspiró los
visuales) cada vez que empieza la partida: `iniciar_partida` y
`cargar_partida` llaman `Sonidos.jingle_inicio()`. Todo es local y tolerante
a fallos: sin mixer, dispositivo o códec devuelve `False` y la partida sigue
en silencio; no toca la `FotoEstado` ni el contrato K5.
