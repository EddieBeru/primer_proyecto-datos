"""Consola interactiva: solo habla con Sesion (igual que Pygame lo hará).

Renderiza la FotoEstado (K5) y traduce texto a `sesion.paso()`. Nunca toca
EstadoPartida, Agenda, budget ni C1 directo: si la consola puede jugar la
partida completa, la fachada tiene todo lo que la vista necesitará (§7.2).
"""

from __future__ import annotations

AYUDA = ("comandos: n/s/e/o mover · abrir <N/S/E/O> · atacar <inst> · esperar · "
         "recoger <id> · usar <id> · soltar <pos|id> · equipar <pos|id> · "
         "deshacer · foto · guardar [ruta] · cargar <ruta> · fin · salir · ayuda")


def renderizar(foto, salida=print) -> None:
    j = foto.jugador
    salida(f"— sala {foto.sala_id} {foto.sala_nombre} [{foto.estado}]")
    puertas = ", ".join(
        f"{d}→{v['destino']}{'🔒' if v['cerrada'] else ''}"
        f"{f'⏳{v.get(\"cierre_en\")}' if v.get('cierre_en') is not None and not v['cerrada'] else ''}"
        for d, v in sorted(foto.puertas.items()))
    salida(f"  puertas: {puertas or '—'}")
    salida(f"  enemigos: {', '.join(f'{e["instancia"]}({e["tipo"][:12]}:{e["vida"]})' for e in foto.enemigos) or '—'}")
    salida(f"  suelo: {', '.join(foto.objetos_suelo) or '—'}")
    trampas = ", ".join(f"{t['instancia']}{'' if t['armada'] else '(off)'}" for t in foto.trampas)
    salida(f"  trampas: {trampas or '—'}")
    salida(f"  vida {j['vida']}/{j['vida_max']} atk {j['ataque']} def {j['defensa']} "
           f"vel {j['velocidad']} efectos {j['efectos'] or '—'}")
    salida(f"  inv: {', '.join(foto.inventario) or '—'} (pergaminos: {foto.pergaminos})")
    for m in foto.mensajes[-5:]:
        salida(f"  · {m}")
    if foto.error:
        salida(f"  ! {foto.error}")
    salida(f"  presupuesto: {foto.presupuesto}")


def bucle(sesion, entrada=input, salida=print, save_default: str = "partida.bin") -> int:
    """Loop bloqueante de consola. Retorna código de salida."""
    salida(AYUDA)
    renderizar(sesion.foto(), salida)
    while True:
        try:
            texto = entrada("> ").strip()
        except (EOFError, KeyboardInterrupt):
            salida("\nsesión interrumpida.")
            return 130
        if not texto:
            continue
        cmd = texto.split()[0].lower()
        if cmd in ("salir", "quit", "exit"):
            res = sesion.finalizar()
            if res.get("terminada"):
                salida(f"fin: {res['estado']} · red: {res.get('red')}")
            else:
                salida("sesión guardada sin terminar? use guardar. adiós.")
            return 0
        if cmd == "fin":
            res = sesion.finalizar()
            salida(str(res))
            if res.get("terminada"):
                return 0
            continue
        if cmd == "ayuda" or cmd == "help":
            salida(AYUDA)
            continue
        if cmd == "foto":
            renderizar(sesion.foto(), salida)
            continue
        if cmd == "guardar":
            partes = texto.split()
            ruta = partes[1] if len(partes) > 1 else save_default
            try:
                sesion.guardar(ruta)
                salida(f"guardada en {ruta}")
            except Exception as e:
                salida(f"! no se pudo guardar: {e}")
            continue
        if cmd == "cargar":
            partes = texto.split()
            if len(partes) < 2:
                salida("! cargar necesita ruta")
                continue
            try:
                renderizar(sesion.cargar(partes[1]), salida)
            except Exception as e:
                salida(f"! no se pudo cargar: {e}")
            continue
        ok, msg, foto = sesion.paso(texto)
        if not ok and msg:
            salida(f"! {msg}")
        elif msg:
            salida(msg)
        renderizar(foto, salida)
        if foto.estado != "jugando":
            res = sesion.finalizar()
            salida(f"fin: {foto.estado} · {res}")
            return 0
