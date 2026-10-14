"""Fachada hacia la Vista (K5): unica puerta entre Vista y Controlador.

La Vista solo envia INTENCIONES (mover, atacar, equipar, ...) y recibe una
FOTO del estado para dibujar. Nunca toca EstadoPartida, Agenda ni C1 directo.
La consola de pruebas (7.2) usa solo esta clase, igual que hara Pygame.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.controller.agenda import Agenda
from src.controller.bitacora import BitacoraMemoria, formatear
from src.controller.combate import ataque_enemigo, ataque_jugador
from src.controller.deshacer import PilaDeshacer, deshacer_una
from src.controller.efectos import (pisar_trampa, usar_antidoto, usar_antorcha, usar_pocion,
                                    ejecutar_fin_efecto, ejecutar_rearme, ejecutar_veneno)
from src.controller.enemigos import comportamiento_de, turno_enemigo
from src.controller.inventario import Inventario, InventarioLlenoError
from src.controller.modelo import EstadoPartida
from src.controller.movimiento import ejecutar_cierre, intentar_mover
from src.controller.reloj import RelojVirtual
from src.controller.victoria import actualizar_estado


@dataclass
class FotoEstado:
    """Lo que la Vista dibuja (K5, seccion 8.2). Solo lectura."""
    sala_id: int
    sala_nombre: str
    puertas: dict = field(default_factory=dict)
    objetos_suelo: list = field(default_factory=list)
    trampas: list = field(default_factory=list)
    jugador: dict = field(default_factory=dict)
    enemigos: list = field(default_factory=list)
    inventario: list = field(default_factory=list)
    equipado: str | None = None
    pergaminos: int = 0
    mensajes: list = field(default_factory=list)
    presupuesto: int = 0
    estado: str = "jugando"
    error: str | None = None
    en_pausa: bool = False


class Fachada:
    """Ventanilla del Controlador. Dibuja con foto(), juega con intenciones."""

    def __init__(self, estado: EstadoPartida, proveedor, catalogo: dict | None = None,
                 bitacora=None) -> None:
        self.estado = estado
        self.proveedor = proveedor
        self.catalogo: dict = catalogo or {}
        self.bitacora = bitacora or BitacoraMemoria()
        self.agenda = Agenda.desde_lista(estado.agenda or [])
        self.reloj = RelojVirtual(ahora=estado.reloj)
        self.pila = PilaDeshacer.desde_lista(estado.pila_deshacer or [])
        self.mensajes: list[str] = []
        self.error: str | None = None
        self.en_pausa = False
        # TODO(C1-3): el presupuesto real lo descuenta C1 por cada peticion; aqui solo se expone.
        # TODO(C1-8): guardar()/cargar() hoy es dict; C1 lo pasara a bytes con struct.

    # -- internos --
    def _sync(self) -> None:
        self.estado.agenda = self.agenda.a_lista()
        self.estado.reloj = self.reloj.ahora
        self.estado.pila_deshacer = self.pila.a_lista()

    def _anotar(self, tipo: str, actor: str, detalle: str = "") -> None:
        try:
            linea = formatear(self.reloj.ahora, tipo, actor, detalle)
        except ValueError:
            return
        try:
            self.bitacora.anotar(linea)
        except Exception:
            pass
        # TODO(C1-9): C1-9 escribe esto a archivo (solo agregar); aqui queda en memoria.
        self.mensajes.append(linea)
        self.mensajes = self.mensajes[-50:]

    def _fail(self, mensaje: str) -> tuple[bool, str]:
        self.error = mensaje
        return False, mensaje

    def _ok(self, mensaje: str = "") -> tuple[bool, str]:
        self.error = None
        if mensaje:
            self.mensajes.append(mensaje)
        self._sync()
        actualizar_estado(self.estado)
        return True, mensaje

    def _tipo_de(self, instancia_id: str) -> str | None:
        for sala in self.estado.salas.values():
            for e in sala.enemigos:
                if e.instancia == instancia_id:
                    return e.tipo_id
        return None

    # -- intenciones de movimiento y puertas (C2-4) --
    def mover(self, direccion: str) -> tuple[bool, str]:
        """Mover N/S/E/O. Programa cierre automatico si abre con llave."""
        # TODO(C2-9): la inversa se apila aqui (origen + puerta + seq de cierre).
        origen = self.estado.sala_actual
        res = intentar_mover(self.estado, direccion, self.proveedor, self.agenda, self.reloj)
        if not res.ok:
            return self._fail(res.mensaje)
        if res.abrio_puerta:
            self._anotar("abrir", "jugador", direccion)
        self.pila.apilar({"op": "mover", "datos": {"origen": origen, "abrio": res.abrio_puerta,
                          "sala_puerta": origen, "direccion": direccion},
                          "eventos": [res.evento_cierre_seq] if res.evento_cierre_seq is not None else []})
        self._anotar("mover", "jugador", direccion)
        return self._ok()

    # -- combate (C2-6) --
    def atacar(self, instancia_id: str) -> tuple[bool, str]:
        tipo = self._tipo_de(instancia_id)
        ficha = self.catalogo.get(tipo) if tipo else None
        atk_e = int(getattr(ficha, "ataque", 0) or 0)
        def_e = int(getattr(ficha, "defensa", 0) or 0)
        suelta = list(getattr(ficha, "suelta", None) or [])
        sala = self.estado.salas.get(self.estado.sala_actual)
        objetivo = next((e for e in (sala.enemigos if sala else []) if e.instancia == instancia_id), None)
        vida_antes = objetivo.vida_actual if objetivo else 0
        res = ataque_jugador(self.estado, instancia_id, atk_e, def_e, suelta, self.catalogo)
        if res.dano == 0 and res.mensaje:
            return self._fail(res.mensaje)
        self.pila.apilar({"op": "dano_enemigo", "datos": {"instancia": instancia_id,
                          "vida_antes": vida_antes, "botin": res.botin}, "eventos": []})
        self._anotar("atacar", "jugador", instancia_id)
        if res.mato:
            self._anotar("muerte", instancia_id, "jugador")
        return self._ok(f"Daño {res.dano}.")

    def ataque_enemigo(self, instancia_id: str) -> tuple[bool, str]:
        """Turno de ataque de un enemigo (lo llama la agenda o la consola)."""
        tipo = self._tipo_de(instancia_id)
        ficha = self.catalogo.get(tipo) if tipo else None
        atk = int(getattr(ficha, "ataque", 0) or 0)
        vida_antes = self.estado.jugador.vida_actual
        res = ataque_enemigo(self.estado, instancia_id, atk, self.catalogo)
        if res.dano == 0 and res.mensaje:
            return self._fail(res.mensaje)
        self.pila.apilar({"op": "dano_jugador", "datos": {"vida_antes": vida_antes}, "eventos": []})
        self._anotar("dano", instancia_id, str(res.dano))
        return self._ok()

    # -- inventario (C2-5) --
    def recoger(self, item_id: str) -> tuple[bool, str]:
        sala = self.estado.salas.get(self.estado.sala_actual)
        if sala is None or item_id not in sala.objetos_suelo:
            return self._fail("No está en el suelo.")
        inv = Inventario.desde_jugador(self.estado.jugador.inventario, self.estado.inventario_max)
        try:
            inv.recoger(item_id)
        except InventarioLlenoError:
            return self._fail(f"Mochila llena ({self.estado.inventario_max}).")
        pos = sala.objetos_suelo.index(item_id)
        sala.objetos_suelo.remove(item_id)
        self.estado.jugador.inventario = inv.a_lista()
        self.pila.apilar({"op": "recoger", "datos": {"item": item_id,
                          "sala": sala.id, "pos_suelo": pos}, "eventos": []})
        self._anotar("recoger", "jugador", item_id)
        return self._ok()

    def soltar(self, pos_o_id) -> tuple[bool, str]:
        inv = Inventario.desde_jugador(self.estado.jugador.inventario, self.estado.inventario_max)
        try:
            if isinstance(pos_o_id, int):
                item = inv.soltar_en(pos_o_id)
                pos = pos_o_id
            else:
                pos = self.estado.jugador.inventario.index(pos_o_id)
                item = inv.soltar_id(pos_o_id)
        except (IndexError, KeyError, ValueError):
            return self._fail("Nada en esa posición.")
        sala = self.estado.salas.get(self.estado.sala_actual)
        sala.objetos_suelo.append(item)
        self.estado.jugador.inventario = inv.a_lista()
        self.pila.apilar({"op": "soltar", "datos": {"item": item,
                          "sala": sala.id, "pos_inv": min(pos, len(self.estado.jugador.inventario))},
                          "eventos": []})
        self._anotar("soltar", "jugador", item)
        return self._ok()

    def equipar(self, pos: int) -> tuple[bool, str]:
        orden_antes = list(self.estado.jugador.inventario)
        inv = Inventario.desde_jugador(orden_antes, self.estado.inventario_max)
        try:
            item = inv.equipar(int(pos))
        except (IndexError, ValueError):
            return self._fail("Nada en esa posición.")
        self.estado.jugador.inventario = inv.a_lista()
        ficha = self.catalogo.get(item)
        if getattr(ficha, "clase", "") == "arma":
            self.estado.jugador.arma_equipada = item
        elif getattr(ficha, "clase", "") == "armadura":
            self.estado.jugador.armadura_equipada = item
        self.pila.apilar({"op": "equipar", "datos": {"orden_antes": orden_antes}, "eventos": []})
        self._anotar("equipar", "jugador", item)
        return self._ok()

    # -- efectos (C2-7) --
    def pisar_trampa(self, instancia_id: str) -> tuple[bool, str]:
        res, inversa = pisar_trampa(self.estado, self.agenda, self.reloj, instancia_id, self.catalogo)
        if not res.ok:
            return self._fail(res.mensaje)
        if inversa:
            self.pila.apilar(inversa)
        self._anotar("efecto", "trampa", instancia_id)
        return self._ok(f"Trampa: {res.dano} de daño.")

    def usar_pocion(self, pocion_id: str) -> tuple[bool, str]:
        res, inversa = usar_pocion(self.estado, self.agenda, self.reloj, pocion_id, self.catalogo)
        if not res.ok:
            return self._fail(res.mensaje)
        if inversa:
            self.pila.apilar(inversa)
        self._anotar("efecto", "jugador", f"pocion:{pocion_id}")
        return self._ok()

    def usar_antidoto(self, antidoto_id: str) -> tuple[bool, str]:
        res, inversa = usar_antidoto(self.estado, self.agenda, antidoto_id)
        if not res.ok:
            return self._fail(res.mensaje)
        if inversa:
            self.pila.apilar(inversa)
        self._anotar("efecto", "jugador", f"antidoto:{antidoto_id}")
        return self._ok(res.mensaje)

    def usar_antorcha(self, antorcha_id: str) -> tuple[bool, str]:
        res, inversa = usar_antorcha(self.estado, self.agenda, self.reloj, antorcha_id, self.catalogo)
        if not res.ok:
            return self._fail(res.mensaje)
        if inversa:
            self.pila.apilar(inversa)
        self._anotar("efecto", "jugador", f"antorcha:{antorcha_id}")
        return self._ok()

    # -- enemigos (C2-8) y reloj (C2-3) --
    def turno_enemigo(self, instancia_id: str) -> tuple[bool, str]:
        msg = turno_enemigo(self.estado, self.agenda, self.reloj, instancia_id, self.catalogo)
        self._anotar("mover", instancia_id, msg)
        self._sync()
        return True, msg

    def avanzar(self) -> str:
        """Ejecuta el proximo evento de la agenda (cierre, veneno, rearme, fin, turno)."""
        ev = self.reloj.avanzar(self.agenda)
        if ev is None:
            return "agenda vacía"
        d = ev.datos or {}
        if ev.tipo == "cierre_puerta":
            ejecutar_cierre(self.estado, d.get("sala"), d.get("direccion"))
        elif ev.tipo == "rearme_trampa":
            ejecutar_rearme(self.estado, d.get("instancia"))
        elif ev.tipo == "veneno":
            ejecutar_veneno(self.estado, int(d.get("dano", 1)))
        elif ev.tipo == "fin_efecto":
            ejecutar_fin_efecto(self.estado, d.get("efecto", ""))
        elif ev.tipo == "turno" and (d.get("kind") == "enemigo" or d.get("actor", "").startswith("e")):
            self.turno_enemigo(d.get("actor"))
        self._sync()
        actualizar_estado(self.estado)
        return ev.tipo

    # -- deshacer (C2-9), pausa, guardar --
    def deshacer(self) -> tuple[bool, str]:
        ok, msg = deshacer_una(self.estado, self.agenda, self.pila, self.catalogo)
        if not ok:
            return self._fail(msg)
        self._anotar("deshacer", "jugador", "")
        return self._ok("Deshecho.")

    def pausar(self) -> None:
        self.en_pausa = True

    def reanudar(self) -> None:
        self.en_pausa = False

    def guardar(self) -> dict:
        self._sync()
        return self.estado.a_dict()

    def cargar(self, data: dict) -> None:
        self.estado = EstadoPartida.desde_dict(data)
        self.agenda = Agenda.desde_lista(self.estado.agenda or [])
        self.reloj = RelojVirtual(ahora=self.estado.reloj)
        self.pila = PilaDeshacer.desde_lista(self.estado.pila_deshacer or [])

    # -- foto K5 (lo unico que la Vista lee) --
    def foto(self) -> FotoEstado:
        sala = self.estado.salas.get(self.estado.sala_actual)
        puertas = {k: {"destino": v.destino, "cerrada": v.cerrada, "llave": v.llave}
                   for k, v in (sala.salidas.items() if sala else {})}
        pergaminos = sum(1 for i in self.estado.jugador.inventario
                         if getattr(self.catalogo.get(i), "clase", "") == "pergamino_retroceso"
                         or "pergamino" in i)
        enemigos = []
        for e in (sala.enemigos if sala else []):
            enemigos.append({"instancia": e.instancia, "tipo": e.tipo_id,
                             "comportamiento": comportamiento_de(self.catalogo, e.tipo_id),
                             "vida": e.vida_actual})
        j = self.estado.jugador
        return FotoEstado(
            sala_id=self.estado.sala_actual, sala_nombre=sala.nombre if sala else "?",
            puertas=puertas, objetos_suelo=list(sala.objetos_suelo) if sala else [],
            trampas=[{"instancia": t.instancia, "tipo": t.tipo_id, "armada": t.armada}
                     for t in (sala.trampas if sala else [])],
            jugador={"vida": j.vida_actual, "vida_max": j.vida_max, "ataque": j.ataque,
                     "defensa": j.defensa, "velocidad": j.velocidad, "efectos": dict(j.efectos)},
            enemigos=enemigos, inventario=list(j.inventario),
            equipado=j.inventario[0] if j.inventario else None, pergaminos=pergaminos,
            mensajes=self.mensajes[-5:], presupuesto=self.estado.presupuesto_restante,
            estado=self.estado.estado, error=self.error, en_pausa=self.en_pausa)

    # -- consola de pruebas 7.2: solo usa la fachada --
    def consola(self, comandos: list[str]) -> list[str]:
        """Ejecuta comandos de texto y devuelve salidas. Plan B si no hay Pygame."""
        salidas = []
        for cmd in comandos:
            p = cmd.strip().split()
            if not p:
                continue
            c = p[0].lower()
            if c in ("n", "s", "e", "o") and len(p) == 1:
                ok, msg = self.mover(c.upper())
                salidas.append(f"mover {c}: {'ok' if ok else msg}")
            elif c == "atacar" and len(p) == 2:
                ok, msg = self.atacar(p[1])
                salidas.append(f"atacar: {msg or 'ok'}")
            elif c == "recoger" and len(p) == 2:
                ok, msg = self.recoger(p[1])
                salidas.append(f"recoger: {'ok' if ok else msg}")
            elif c == "soltar" and len(p) == 2:
                ok, msg = self.soltar(int(p[1]) if p[1].isdigit() else p[1])
                salidas.append(f"soltar: {'ok' if ok else msg}")
            elif c == "equipar" and len(p) == 2:
                ok, msg = self.equipar(int(p[1]))
                salidas.append(f"equipar: {'ok' if ok else msg}")
            elif c == "deshacer":
                ok, msg = self.deshacer()
                salidas.append(f"deshacer: {'ok' if ok else msg}")
            elif c == "avanzar":
                salidas.append(f"evento: {self.avanzar()}")
            elif c == "foto":
                f = self.foto()
                salidas.append(f"sala {f.sala_id} {f.sala_nombre} vida {f.jugador['vida']} inv {f.inventario} estado {f.estado}")
            else:
                salidas.append(f"¿{cmd}?")
        return salidas
