"""Consola interactiva: solo habla con Sesion (igual que Pygame lo hará).

Renderiza la FotoEstado (K5) y traduce texto a `sesion.paso()`. Nunca toca
EstadoPartida, Agenda, budget ni C1 directo: si la consola puede jugar la
partida completa, la fachada tiene todo lo que la vista necesitará (§7.2).
"""

from __future__ import annotations

import select
import sys
import time

from src.controller1.mergesort import mergesort

AYUDA = ("comandos: n/s/e/o mover · abrir <N/S/E/O> · atacar <inst> · esperar · "
         "pisar <inst> · recoger <id> · usar <id> · soltar <pos|id> · equipar <pos|id> · "
         "inventario [nombre|peso|valor] · mapa · ir a <id> · cancelar · "
         "deshacer · historia <t|#k> · foto · guardar [ruta] · "
         "cargar <ruta> · fin · salir · ayuda")


def _cierre_puerta(v) -> str:
    cierre = v.get("cierre_en")
    if cierre is not None and not v["cerrada"]:
        return f"\u23f3{cierre}"
    return ""


def _etiqueta_enemigo(e) -> str:
    return f"{e['instancia']}({e['tipo'][:12]}:{e['vida']})"


def renderizar(foto, salida=print) -> None:
    j = foto.jugador
    salida(f"— sala {foto.sala_id} {foto.sala_nombre} [{foto.estado}]")
    puertas = ", ".join(
        f"{d}\u2192{v['destino']}{'\U0001f512' if v['cerrada'] else ''}{_cierre_puerta(v)}"
        for d, v in mergesort(foto.puertas.items(), clave=lambda kv: kv[0]))
    salida(f"  puertas: {puertas or '—'}")
    salida(f"  enemigos: {', '.join(_etiqueta_enemigo(e) for e in foto.enemigos) or '—'}")
    salida(f"  suelo: {', '.join(foto.objetos_suelo) or '—'}")
    trampas = ", ".join(f"{t['instancia']}{'' if t['armada'] else '(off)'}" for t in foto.trampas)
    salida(f"  trampas: {trampas or '—'}")
    # Mejoras 2026-10: aviso de sala oscura (la API puede marcarlas).
    if getattr(foto, "sala_oscura", False):
        try:
            con_luz = int((j.get("efectos") or {}).get("antorcha", 0) or 0) > 0
        except (TypeError, ValueError):
            con_luz = False
        salida("  oscuridad: " + ("iluminada por tu antorcha" if con_luz
                                  else "a oscuras; enciende una antorcha (usar <id>)"))
    salida(f"  vida {j['vida']}/{j['vida_max']} atk {j['ataque']} def {j['defensa']} "
           f"vel {j['velocidad']} efectos {j['efectos'] or '—'}")
    viaje = getattr(foto, "viaje", None) or {}
    if viaje.get("activo"):
        salida(f"  viaje: hacia {viaje.get('destino')} · cancelar para detener")
    elif viaje.get("motivo"):
        salida(f"  viaje detenido: {viaje['motivo']}")
    salida(f"  inv: {', '.join(foto.inventario) or '—'} (pergaminos: {foto.pergaminos})")
    for m in foto.mensajes[-20:]:  # §4.8: se conservan los últimos 20
        salida(f"  · {m}")
    if foto.error:
        salida(f"  ! {foto.error}")
    salida(f"  presupuesto: {foto.presupuesto}")


def bucle(sesion, entrada=input, salida=print, save_default: str = "partida.bin",
          *, leer_viaje=None, reloj=time.monotonic) -> int:
    """Loop de consola; mientras hay viaje acepta consultas/cancelación sin bloquear."""
    salida(AYUDA)
    renderizar(sesion.foto(), salida)
    prompt_viaje = False
    proximo_paso = reloj() + 0.15
    while True:
        try:
            if sesion.fachada and sesion.fachada.viaje.activo and (entrada is input or leer_viaje is not None):
                espera = max(0.0, proximo_paso - reloj())
                if leer_viaje is not None:
                    texto = leer_viaje(espera)  # None: vence plazo; "": EOF.
                else:
                    if not prompt_viaje:
                        sys.stdout.write("> ")
                        sys.stdout.flush()
                        prompt_viaje = True
                    listo, _, _ = select.select([sys.stdin], [], [], espera)
                    texto = sys.stdin.readline() if listo else None
                if texto is None:
                    if reloj() >= proximo_paso:
                        _, _, foto = sesion.avanzar_viaje()
                        renderizar(foto, salida)
                        proximo_paso = reloj() + 0.15
                    continue
                if not texto:
                    raise EOFError
                texto = texto.strip()
                prompt_viaje = False
            else:
                texto = entrada("> ").strip()
        except (EOFError, KeyboardInterrupt):
            sesion.paso("cancelar")
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
        if cmd == "historia":
            ok, mensaje, _ = sesion.paso(texto)
            salida(mensaje if ok else "! " + mensaje)
            continue
        if cmd == "mapa":
            mapa = sesion.mapa_conocido()
            for sala in mapa.salas:
                salida(f"{sala['id']}  {sala.get('nombre') or sala.get('etiqueta')}  [{sala.get('estado')}]")
                for puerta in sala.get("salidas", ()):
                    salida(f"  {puerta['direccion']}→{puerta['destino']} costo {puerta['costo']} [{puerta['estado']}]")
            continue
        if cmd in ("inventario", "inv"):
            partes = texto.split()
            criterio = partes[1] if len(partes) > 1 else "nombre"
            orden = sesion.inventario_ordenado(criterio)
            salida(f"inv ({criterio}): {', '.join(orden) or '—'}")
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
        if cmd == "ir" and ok:
            proximo_paso = reloj() + 0.15
        if not ok and msg:
            salida(f"! {msg}")
        elif msg:
            salida(msg)
        renderizar(foto, salida)
        if foto.estado != "jugando":
            res = sesion.finalizar()
            salida(f"fin: {foto.estado} · {res}")
            return 0
